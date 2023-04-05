#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#


from quackhunt.engine import (
    Game,
    EngineConfig,
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

    def overdraw(self, screen: pygame.Surface) -> None:
        self.position[0] += self.velocity[0] * self.dt
        self.position[1] += self.velocity[1] * self.dt

        if self.position[0] > screen.get_width():
            self.position[0] = -50

        pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(self.position[0], self.position[1], 50, 50))


def run():
    run_game(QuackHunt())
