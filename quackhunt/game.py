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
)

RENDER_WIDTH = 1920
RENDER_HEIGHT = 1080
RENDER_ORIGIN = Vec2(RENDER_WIDTH, RENDER_HEIGHT) / 2


def rand() -> float:
    return random.random()


def circle_collision(point: Vec2, position: Vec2, radius: float) -> bool:
    return point.distance_squared_to(position) < radius * radius


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
    fire_sound_node: SoundNode

    def __init__(self):
        super().__init__(
            name='crosshair',
            filename='./assets/gfx/crosshair.png',
            position=RENDER_ORIGIN,
        )

        self.fire_sound_node = SoundNode(filename='./assets/sfx/fire.wav')
        self.add_child(self.fire_sound_node)

    def update(self, game: 'QuackHunt') -> None:
        self.position = game.aim_position

        for e in game.native_events:
            if e.type == pyg.MOUSEMOTION:
                self.position = Vec2(e.pos)
                game.aim_position = self.position
                break

        for name, data in game.events:
            if name == 'shot_fired':
                self.fire_sound_node.play()


class DuckNode(Node):
    radius: float
    movement: Vec2
    is_hit: bool

    def __init__(self):
        super().__init__()

        self.radius = 80
        self.movement = Vec2(100, -400)
        self.position = Vec2(700, 700)
        self.is_hit = False

    def update(self, game: 'Game') -> None:
        if not self.is_hit:
            for name, data in game.events:
                if name == 'shot_fired':
                    if circle_collision(data.position, self.position, self.radius):
                        game.engine.queue_event('duck_hit')
                        self.is_hit = True

        self.position += self.movement * game.dt

        if self.position.y < -100:
            self.position = Vec2(700, 700)
            self.is_hit = False

    def draw(self, surface: pyg.Surface, offset: Vec2) -> None:
        color = 0xFF0000 if self.is_hit else 0x00FF00
        pyg.draw.circle(surface, color, self.position, self.radius, width=8)


class DrumNode(SpriteNode):
    round_nodes: List[SpriteNode]

    def __init__(self):
        super().__init__(filename='./assets/gfx/drum.png')
        self.position = Vec2(self.size.x / 2 + 20, RENDER_HEIGHT - self.size.y / 2 - 20)
        self.round_nodes = []

        for i in range(6):
            self.round_nodes.append(SpriteNode(
                filename='./assets/gfx/round.png',
                position=Vec2(math.cos(math.tau / 6 * (i - 1) - (math.pi / 6)) * 75,
                              math.sin(math.tau / 6 * (i - 1) - (math.pi / 6)) * 75),
            ))

        self.add_child(*self.round_nodes)

    def update(self, game: 'QuackHunt') -> None:
        for i in range(6 - game.rounds_left):
            self.round_nodes[i].visible = False


class UINode(Node):
    def __init__(self):
        super().__init__()

        self.score_node = TextNode(None, 200, position=Vec2(RENDER_WIDTH - 400, RENDER_HEIGHT - 200))
        self.add_child(
            DrumNode(),
            self.score_node,
        )

    def update(self, game: 'QuackHunt') -> None:
        self.score_node.text = str(game.score).ljust(4, '0')


class GameLogicNode(Node):
    def pull_trigger(self, game: 'QuackHunt') -> None:
        if game.rounds_left == 0:
            return

        game.rounds_left -= 1
        game.engine.queue_event('shot_fired', position=game.aim_position)

    def duck_hit(self, game: 'QuackHunt') -> None:
        game.score += 1000

    def update(self, game: 'QuackHunt') -> None:
        for e in game.native_events:
            if e.type == pyg.MOUSEBUTTONDOWN and e.button == 1:
                self.pull_trigger(game)
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
    score: int = 0

    def __init__(self):
        self.aim_position = Vec2()

    def get_config(self) -> EngineConfig:
        return EngineConfig(
            title='Quack Hunt',
            width=RENDER_WIDTH,
            height=RENDER_HEIGHT,
            target_fps=60,
            show_cursor=True,
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
            BackgroundNode(),
            DuckNode(),
            ForegroundNode(),
            UINode(),
            CrosshairNode(),
        )

        self.detection_thread = Thread(
            target=detection_runner,
            daemon=True,
            args=[self],
        )

        self.detection_thread.start()

    def on_stopped(self) -> None:
        self.detection_thread.join()

    def on_frame_start(self) -> None:
        self.engine.set_title(str(round(self.engine.clock.get_fps())))


def run():
    run_game(QuackHunt())
