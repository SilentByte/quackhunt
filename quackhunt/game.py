#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#

from threading import Thread

from quackhunt import config
from quackhunt.detector import (
    Detector,
    DetectionResult,
)
from quackhunt.engine import (
    Game,
    EngineConfig,
    SpriteNode,
    SoundNode,
    Vec2,
    run_game,
)

RENDER_WIDTH = 1920
RENDER_HEIGHT = 1080
RENDER_ORIGIN = Vec2(RENDER_WIDTH, RENDER_HEIGHT) / 2


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
            if e.type == game.pyg.MOUSEMOTION:
                self.position = Vec2(e.pos)
                game.aim_position = self.position
                break

        for name, data in game.events:
            if name == 'fire':
                self.fire_sound_node.play()


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
    )

    while game.is_running:
        detection = detector.process_frame()
        game.update_detection(detection)


class QuackHunt(Game):
    detection_thread: Thread = None
    aim_position: Vec2 = RENDER_ORIGIN

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
                (detection_result.primary_detection[0]/2+0.5) * RENDER_WIDTH,
                (detection_result.primary_detection[1]/2+0.5) * RENDER_HEIGHT,
            )

    def fire(self) -> None:
        self.engine.queue_event('fire')

    def on_started(self) -> None:
        self.scene_graph.add_child(
            BackgroundNode(),
            ForegroundNode(),
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
