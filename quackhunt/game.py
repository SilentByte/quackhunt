#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#

import math
import random
from threading import Thread
from typing import List

from quackhunt import config
from quackhunt.detector import (
    Detector,
    DetectionResult,
)
from quackhunt.engine import (
    pyg,
    Game,
    EngineConfig,
    Node,
    SpriteNode,
    TextNode,
    SoundNode,
    Vec2,
    run_game,
    load_texture,
)

RENDER_WIDTH = 1920.0
RENDER_HEIGHT = 1080.0

RENDER_ORIGIN = Vec2(RENDER_WIDTH, RENDER_HEIGHT) / 2


def rand_float(start: float = 0, end: float = 1.0) -> float:
    return start + (random.random() * (end - start))


def rand_bool() -> bool:
    return rand_float() > 0.5


def rand_choice(choices: List):
    return random.choice(choices)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def circle_collision(point: Vec2, position: Vec2, radius: float) -> bool:
    return point.distance_squared_to(position) < radius * radius


def format_time(seconds: float) -> str:
    minutes, seconds = divmod(seconds, 60)
    return f'{minutes:0>2.0f}:{seconds:0>2.0f}'


class SkyNode(SpriteNode):
    def __init__(self):
        super().__init__(filename='./assets/gfx/sky.png')

    def update(self, game: 'Game') -> None:
        self.position.x += 20 * game.dt

    def draw(self, surface: pyg.Surface, offset: Vec2) -> None:
        if self.position.x > RENDER_WIDTH:
            self.position.x -= 2 * RENDER_WIDTH

        surface.blit(self.texture, self.position)
        surface.blit(self.texture, Vec2(self.position.x - 2 * RENDER_WIDTH, self.position.y))


class BackgroundNode(SpriteNode):
    def __init__(self):
        super().__init__(
            filename='./assets/gfx/background.png',
            position=RENDER_ORIGIN,
        )


class ForegroundNode(SpriteNode):
    def __init__(self):
        super().__init__(
            filename='./assets/gfx/foreground.png',
            position=RENDER_ORIGIN,
        )


class CrosshairNode(SpriteNode):
    def __init__(self):
        super().__init__(
            name='crosshair',
            filename='./assets/gfx/crosshair.png',
            position=RENDER_ORIGIN,
        )

    def update(self, game: 'QuackHunt') -> None:
        self.position = game.aim_position

        for e in game.native_events:
            if e.type == pyg.MOUSEMOTION:
                self.position = Vec2(e.pos)
                game.aim_position = self.position
                break


class HitNode(Node):
    def remove_tag(self, child: Node):
        self.remove_child(child)
        pass

    def update(self, game: 'QuackHunt') -> None:
        for name, data in game.events:
            if name == 'duck_hit':
                child = SpriteNode(filename='./assets/gfx/hit.png', position=data.position)
                self.add_child(child)
                game.engine.queue_timer_event(1, self.remove_tag, child=child)
                break

        for child in self.children:
            child.position.y -= 100 * game.dt


class DuckNode(Node):
    radius: float
    movement: Vec2
    fall_movement: Vec2
    is_hit: bool

    def __init__(self):
        super().__init__()

        self.radius = 80
        self.reset()

        self.falling_sound_node = SoundNode(filename='./assets/sfx/duck_falling.wav')

        self.animation_left_textures = [
            load_texture('./assets/gfx/duck_left_1.png'),
            load_texture('./assets/gfx/duck_left_2.png'),
        ]

        self.animation_right_textures = [
            load_texture('./assets/gfx/duck_right_1.png'),
            load_texture('./assets/gfx/duck_right_2.png'),
        ]

        self.animation_dead_textures = [
            load_texture('./assets/gfx/duck_dead_left.png'),
            load_texture('./assets/gfx/duck_dead_right.png'),
        ]

        self.size = Vec2(self.animation_left_textures[0].get_size())
        self.current_frame = None

    def reset(self):
        self.is_hit = False
        self.fall_movement = Vec2(0, rand_choice([200, 300, 400]))

        spawn_y = rand_float(700, 900)

        if rand_bool():
            spawn_x = rand_float(0, RENDER_WIDTH / 2)
            self.movement = Vec2(rand_float(200, 400), -rand_float(200, 600))
        else:
            spawn_x = rand_float(RENDER_WIDTH / 2, RENDER_WIDTH)
            self.movement = Vec2(-rand_float(200, 400), -rand_float(200, 600))

        self.position = Vec2(spawn_x, spawn_y)

    def next_frame(self, game: 'QuackHunt'):
        frame_index = int(game.engine.get_time() * 5) % len(self.animation_left_textures)

        if self.is_hit:
            self.current_frame = self.animation_dead_textures[frame_index]
        elif self.movement.x < 0:
            self.current_frame = self.animation_left_textures[frame_index]
        else:
            self.current_frame = self.animation_right_textures[frame_index]

    def update(self, game: 'QuackHunt') -> None:
        if not self.is_hit and not game.is_duck_hit:
            for name, data in game.events:
                if name == 'shot_fired':
                    if circle_collision(data.position, self.position, self.radius):
                        game.is_duck_hit = True
                        game.engine.queue_event('duck_hit', position=self.position.copy())

                        self.is_hit = True
                        self.falling_sound_node.play()

        self.next_frame(game)

        if self.is_hit:
            self.position += self.fall_movement * game.dt
        else:
            self.position += self.movement * game.dt

        if self.position.y < -100:
            self.reset()

        if self.is_hit and self.position.y > RENDER_HEIGHT - 100:
            self.remove()

    def draw(self, surface: pyg.Surface, offset: Vec2) -> None:
        # color = 0xFF0000 if self.is_hit else 0x00FF00
        # pyg.draw.circle(surface, color, self.position, self.radius, width=8)
        surface.blit(self.current_frame, self.get_adjusted_rect(offset))


class DrumNode(SpriteNode):
    round_nodes: List[SpriteNode]

    def __init__(self):
        super().__init__(filename='./assets/gfx/drum.png')

        self.impulse = 0.0
        self.position = Vec2(self.size.x / 2 + 20, RENDER_HEIGHT - self.size.y / 2 - 20)
        self.round_nodes = []

        for i in range(6):
            self.round_nodes.append(SpriteNode(
                filename='./assets/gfx/round.png',
                position=Vec2(math.cos(math.tau / 6 * (i - 1) - (math.pi / 6)) * 65,
                              math.sin(math.tau / 6 * (i - 1) - (math.pi / 6)) * 65),
            ))

        self.add_child(*self.round_nodes)

    def update(self, game: 'QuackHunt') -> None:
        for name, data in game.events:
            if name == 'shot_fired':
                self.impulse = 30
                break

        for i in range(6):
            self.round_nodes[i].visible = 6 - game.rounds_left <= i

        self.impulse = max(self.impulse - 100 * game.dt, 0)

    def draw(self, surface: pyg.Surface, offset: Vec2) -> None:
        offset = Vec2(offset.x + rand_float(-1, 1) * self.impulse, offset.y + rand_float(-1, 1) * self.impulse)
        surface.blit(self.texture, self.get_adjusted_rect(offset))


class DigitNode(SpriteNode):
    GLPYPHS = {
        ' ': 0,
        '0': 1,
        '1': 2,
        '2': 3,
        '3': 4,
        '4': 5,
        '5': 6,
        '6': 7,
        '7': 8,
        '8': 9,
        '9': 10,
        ':': 11,
    }

    text: str = ''

    def __init__(self, position: Vec2):
        super().__init__(filename='./assets/gfx/digits.png',
                         position=position)

    def draw(self, surface: pyg.Surface, offset: Vec2) -> None:
        text_offset = Vec2()
        for c in self.text:
            digit_x = DigitNode.GLPYPHS.get(c, 0) * self.size.y
            text_offset.x += self.size.y
            surface.blit(self.texture, offset + self.position + text_offset, (digit_x, 0, self.size.y, self.size.y))


class UINode(Node):
    def __init__(self):
        super().__init__()

        self.time_node = DigitNode(position=Vec2(RENDER_WIDTH - 640, RENDER_HEIGHT - 250))
        self.score_node = DigitNode(position=Vec2(RENDER_WIDTH - 640, RENDER_HEIGHT - 130))
        self.add_child(
            DrumNode(),
            self.time_node,
            self.score_node,
        )

    def update(self, game: 'QuackHunt') -> None:
        self.time_node.text = format_time(game.engine.get_time())
        self.score_node.text = str(game.score).rjust(5, '0')


class GameLogicNode(Node):
    fire_sound_node: SoundNode
    cock_sound_node: SoundNode
    reload_sound_node: SoundNode

    def __init__(self):
        super().__init__()
        self.fire_sound_node = SoundNode(filename='./assets/sfx/fire.wav')
        self.cock_sound_node = SoundNode(filename='./assets/sfx/cock.wav')
        self.reload_sound_node = SoundNode(filename='./assets/sfx/reload.wav')

    def reload(self, game: 'QuackHunt') -> None:
        game.rounds_left = 6
        game.can_fire = True
        self.reload_sound_node.play()

    def cock(self, game: 'QuackHunt') -> None:
        game.can_fire = True
        self.cock_sound_node.play()

    def trigger_pulled(self, game: 'QuackHunt') -> None:
        if not game.can_fire or game.rounds_left == 0:
            return

        if game.rounds_left == 1:
            game.engine.queue_timer_event(1, self.reload, game=game)

        game.rounds_left -= 1
        game.can_fire = False
        game.engine.queue_event('shot_fired', position=game.aim_position)
        self.fire_sound_node.play()

        if game.rounds_left > 0:
            game.engine.queue_timer_event(0.6, self.cock, game=game)

    def duck_hit(self, game: 'QuackHunt') -> None:
        game.score += 120

    def update(self, game: 'QuackHunt') -> None:
        game.is_duck_hit = False

        for e in game.native_events:
            if e.type == pyg.MOUSEBUTTONDOWN and e.button == 1:
                self.trigger_pulled(game)
                break

        for name, data in game.events:
            if name == 'duck_hit':
                self.duck_hit(game)


def detection_runner(game: 'QuackHunt'):
    config_data = config.load_config()
    detector = Detector(
        video_capture_index=config_data.video_capture_index,
        flip_vertically=config_data.flip_vertically,
        flip_horizontally=config_data.flip_horizontally,
        show_debug_windows=config_data.show_debug_windows,
        primary_lower_threshold=config_data.primary_lower_threshold,
        primary_upper_threshold=config_data.primary_upper_threshold,
        primary_min_confidence=config_data.primary_min_confidence,
        secondary_lower_threshold=config_data.secondary_lower_threshold,
        secondary_upper_threshold=config_data.secondary_upper_threshold,
        secondary_min_confidence=config_data.secondary_min_confidence,
        stretch_factors=config_data.stretch_factors,
        nudge_addends=config_data.nudge_addends,
    )

    while game.is_running:
        detection = detector.process_frame()
        game.update_detection(detection)


class QuackHunt(Game):
    detection_thread: Thread = None
    aim_position: Vec2 = RENDER_ORIGIN
    rounds_left: int = 6
    can_fire: bool = True
    is_duck_hit: bool = False
    score: int = 0

    def __init__(self):
        self.aim_position = Vec2()

    def get_config(self) -> EngineConfig:
        return EngineConfig(
            title='Quack Hunt',
            width=int(RENDER_WIDTH),
            height=int(RENDER_HEIGHT),
            target_fps=60,
            show_cursor=False,
        )

    def update_detection(self, detection_result: DetectionResult) -> None:
        if detection_result.primary_detection is not None:
            self.aim_position = Vec2(
                (detection_result.primary_detection[0] / 2 + 0.5) * RENDER_WIDTH,
                (detection_result.primary_detection[1] / 2 + 0.5) * RENDER_HEIGHT,
            )

    def on_started(self) -> None:
        self.scene_graph.add_child(
            GameLogicNode(),
            SkyNode(),
            BackgroundNode(),
            DuckNode(),
            DuckNode(),
            DuckNode(),
            DuckNode(),
            DuckNode(),
            DuckNode(),
            DuckNode(),
            DuckNode(),
            ForegroundNode(),
            HitNode(),
            UINode(),
            CrosshairNode(),
        )

        # self.detection_thread = Thread(
        #     target=detection_runner,
        #     daemon=True,
        #     args=[self],
        # )
        #
        # self.detection_thread.start()

    # def on_stopped(self) -> None:
    #     self.detection_thread.join()

    def on_frame_start(self) -> None:
        fps = round(self.engine.clock.get_fps())
        self.engine.set_title(f'Quack Hunt ({fps})')


def run():
    run_game(QuackHunt())
