#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#

from quackhunt.engine import (
    Game,
    EngineConfig,
    Node,
    RectNode,
    Vec2,
    run_game,
)


class MovingRect(Node):
    velocity = Vec2(400, 0)

    def __init__(self):
        super().__init__(position=Vec2(100, 100))

        self.add_child(
            RectNode('rect', Vec2(0, 0), Vec2(100, 100), 0xFF00FF).add_child(
                RectNode('sub', Vec2(0, 0), Vec2(50, 50), 0x00FF00),
            )
        )

    def update(self, game: Game) -> None:
        keys = game.pyg.key.get_pressed()

        if keys[game.pyg.K_LEFT]:
            self.position += -self.velocity * game.dt

        if keys[game.pyg.K_RIGHT]:
            self.position += self.velocity * game.dt

        if self.position[0] > game.engine.screen_surface.get_width():
            self.position[0] = -self.size.x / 2


class QuackHunt(Game):
    def get_config(self) -> EngineConfig:
        return EngineConfig(
            title='Quack Hunt',
            width=1920,
            height=1080,
            target_fps=60,
        )

    def on_start(self) -> None:
        self.scene_graph.add_child(
            MovingRect()
        )


def run():
    run_game(QuackHunt())
