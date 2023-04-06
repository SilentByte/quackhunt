#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#
import pygame

from quackhunt.engine import (
    Game,
    EngineConfig,
    Node,
    RectNode,
    SpriteNode,
    SoundNode,
    Vec2,
    run_game,
)


class MovingRect(Node):
    def __init__(self):
        super().__init__(position=Vec2(100, 100))

        self.add_child(
            RectNode('rect', Vec2(0, 0), Vec2(200, 200), 0xFF00FF).add_child(
                RectNode('sub', Vec2(0, 0), Vec2(50, 50), 0x00FF00),
                SoundNode('./assets/sfx/shot.wav', 'fire_sound'),
            )
        )

    def update(self, game: Game) -> None:
        keys = game.pyg.key.get_pressed()
        movement = Vec2()

        if keys[game.pyg.K_LEFT]:
            movement.x -= 1

        if keys[game.pyg.K_RIGHT]:
            movement.x += 1

        if keys[game.pyg.K_UP]:
            movement.y -= 1

        if keys[game.pyg.K_DOWN]:
            movement.y += 1

        if movement:
            movement.normalize_ip()
            self.position += 1200 * movement * game.dt

        if self.position[0] > game.engine.screen_surface.get_width():
            self.position[0] = -self.size.x / 2
            self.find_child('rect/fire_sound').play()


RENDER_WIDTH = 1920
RENDER_HEIGHT = 1080
RENDER_ORIGIN = Vec2(RENDER_WIDTH, RENDER_HEIGHT) / 2


class QuackHunt(Game):
    def get_config(self) -> EngineConfig:
        return EngineConfig(
            title='Quack Hunt',
            width=RENDER_WIDTH,
            height=RENDER_HEIGHT,
            target_fps=60,
        )

    def on_start(self) -> None:
        self.scene_graph.add_child(
            SpriteNode('./assets/gfx/background.png', position=RENDER_ORIGIN),
            MovingRect(),
            SpriteNode('./assets/gfx/foreground.png', position=RENDER_ORIGIN),
        )

    def on_frame_start(self) -> None:
        self.engine.set_title(str(round(self.engine.clock.get_fps())))


def run():
    run_game(QuackHunt())
