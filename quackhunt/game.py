#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#

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
    def __init__(self):
        super().__init__(
            name='crosshair',
            filename='./assets/gfx/crosshair.png',
            position=RENDER_ORIGIN,
        )

    def update(self, game: 'QuackHunt') -> None:
        self.position = game.aim_position

        for e in game.events:
            if e.type == game.pyg.MOUSEMOTION:
                self.position = Vec2(e.pos)
                game.aim_position = self.position
                break


class QuackHunt(Game):
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

    def update_aim(self, x: float, y: float) -> None:
        self.aim_position = Vec2(x * RENDER_WIDTH, y * RENDER_HEIGHT)

    def fire(self) -> None:
        self.scene_graph.root_node.find_child('fire_sound').play()

    def on_start(self) -> None:
        self.scene_graph.add_child(
            BackgroundNode(),
            ForegroundNode(),
            CrosshairNode(),
            SoundNode(name='fire_sound', filename='./assets/sfx/fire.wav')
        )

    def on_stop(self) -> None:
        pass

    def on_frame_start(self) -> None:
        self.engine.set_title(str(round(self.engine.clock.get_fps())))


def run():
    run_game(QuackHunt())
