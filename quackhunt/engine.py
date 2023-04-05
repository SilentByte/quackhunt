#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#

from collections import OrderedDict
from dataclasses import dataclass
from typing import List, Any

import pygame


@dataclass
class EngineConfig:
    title: str = 'Quack Hunt Engine'
    width: int = 1920
    height: int = 1080
    target_fps: int = 60
    clear_color: int = 0x111111


NodeDict = OrderedDict

Vec2 = pygame.Vector2
SimpleRect = tuple[int | float, int | float, int | float, int | float]


class Node:
    name: str
    children: NodeDict[str, 'Node']
    position: Vec2
    size: Vec2

    def __init__(self, name: str, position: Vec2 = Vec2(), size: Vec2 = Vec2()):
        self.name = name
        self.children = NodeDict()
        self.position = position

    def add_child(self, *nodes: 'Node') -> 'Node':
        for node in nodes:
            self.children[node.name] = node

        return self

    def get_adjusted_rect(self, offset: Vec2) -> SimpleRect:
        return (
            self.position.x - self.size.x / 2 + offset.x,
            self.position.y - self.size.y / 2+offset.y,
            self.size.x,
            self.size.y,
        )

    def draw(self, surface: pygame.Surface, offset: Vec2) -> None:
        pass


class RectNode(Node):
    color: int

    def __init__(
            self,
            name: str,
            position: Vec2,
            size: Vec2,
            color: int = 0xFFFFFF,
    ):
        super().__init__(name, position)

        self.size = size
        self.color = color

    def draw(self, surface: pygame.Surface, offset: Vec2) -> None:
        pygame.draw.rect(surface, self.color, self.get_adjusted_rect(offset))


class SceneGraph:
    root_node: Node

    def __init__(self):
        self.root_node = Node('root')

    def add_child(self, *nodes: Node) -> 'Node':
        for node in nodes:
            self.root_node.add_child(node)

        return self.root_node

    def draw(self, surface: pygame.Surface) -> None:
        def draw_inner(node: Node, offset: Vec2) -> None:
            node.draw(surface, offset)
            for child_node in node.children.values():
                draw_inner(child_node, node.position)

        draw_inner(self.root_node, self.root_node.position)


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
    _screen_surface: pygame.Surface
    _clock: pygame.time.Clock
    _target_fps: int
    _clear_color: int
    _scene_graph: SceneGraph

    def __init__(self, config: EngineConfig):
        pygame.init()
        pygame.mixer.init()

        self._screen_surface = pygame.display.set_mode((config.width, config.height), pygame.RESIZABLE | pygame.SCALED)
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

            self._screen_surface.fill(self._clear_color)

            self._scene_graph.draw(self._screen_surface)

            game.overdraw(self._screen_surface)

            pygame.display.flip()


def run_game(game: Game) -> None:
    _Engine(game.get_config()).run(game)
