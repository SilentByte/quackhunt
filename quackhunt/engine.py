#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#


from dataclasses import dataclass

import pygame


@dataclass
class EngineConfig:
    title: str = 'Quack Hunt Engine'
    width: int = 1920
    height: int = 1080
    target_fps: int = 60
    clear_color: int = 0x111111


class SceneGraph:
    pass


# noinspection PyMethodMayBeStatic
class Game:
    engine: '_Engine'
    scene_graph: SceneGraph
    dt: float

    def get_config(self) -> EngineConfig:
        return EngineConfig(
            title='Game',
            width=1920,
            height=1080,
            target_fps=60,
            clear_color=0x111111,
        )

    def on_start(self) -> None:
        pass

    def on_stop(self) -> None:
        pass

    def overdraw(self, screen: pygame.display) -> None:
        """
        Mainly useful for quick debug rendering.
        """
        pass


# noinspection PyMethodMayBeStatic
class _Engine:
    _screen: pygame.Surface
    _clock: pygame.time.Clock
    _target_fps: int
    _clear_color: int
    _scene_graph: SceneGraph

    def __init__(self, config: EngineConfig):
        pygame.init()
        pygame.mixer.init()

        self._screen = pygame.display.set_mode((config.width, config.height), pygame.RESIZABLE | pygame.SCALED)
        self._clock = pygame.time.Clock()
        self._target_fps = config.target_fps
        self._clear_color = config.clear_color
        self._scene_graph = SceneGraph()

        self.set_title(config.title)

    def _shutdown(self) -> None:
        pygame.quit()

    def set_title(self, title: str) -> None:
        pygame.display.set_caption(title)

    def get_fps(self) -> float:
        return self._clock.get_fps()

    def get_spf(self) -> float:
        return 1.0 / self._clock.get_fps()

    def _handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        return True

    def run(self, game: Game) -> None:
        game.scene_graph = self._scene_graph
        game.on_start()

        while True:
            if not self._handle_events():
                game.on_stop()
                self._shutdown()
                break

            game.dt = self._clock.tick(self._target_fps) / 1000.0

            self._screen.fill(self._clear_color)

            # TODO: Render Scene Graph.
            game.overdraw(self._screen)

            pygame.display.flip()


def run_game(game: Game) -> None:
    _Engine(game.get_config()).run(game)
