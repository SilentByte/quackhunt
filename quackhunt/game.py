#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#


from quackhunt.engine import (
    Game,
    EngineConfig,
    RectNode,
    Vec2,
    run_game,
)

import pygame


class QuackHunt(Game):
    position = [-50, 300]
    velocity = [200, 0]

    def get_config(self) -> EngineConfig:
        return EngineConfig(
            title='Quack Hunt',
            width=1920,
            height=1080,
            target_fps=60,
        )

    def on_start(self) -> None:
        self.scene_graph.add_child(
            RectNode('rect', Vec2(100, 100), Vec2(100, 100), 0xFF00FF).add_child(
                RectNode('sub', Vec2(0, 0), Vec2(50, 50), 0x00FF00),
            ),
        )

    def overdraw(self, screen: pygame.Surface) -> None:
        self.position[0] += self.velocity[0] * self.dt
        self.position[1] += self.velocity[1] * self.dt

        if self.position[0] > screen.get_width():
            self.position[0] = -50

        pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(self.position[0], self.position[1], 50, 50))


def run():
    run_game(QuackHunt())
