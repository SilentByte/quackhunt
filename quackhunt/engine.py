#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#

from dataclasses import dataclass
from typing import List

import pygame


def _global_id() -> int:
    _global_id.counter += 1
    return _global_id.counter


_global_id.counter = 0


@dataclass
class EngineConfig:
    title: str = 'Quack Hunt Engine'
    width: int = 1920
    height: int = 1080
    target_fps: int = 60
    clear_color: int = 0x111111


Vec2 = pygame.Vector2
SimpleRect = tuple[int | float, int | float, int | float, int | float]


class Node:
    id: int
    name: str
    children: List['Node']
    position: Vec2
    size: Vec2

    def __init__(self, name: str = '', position: Vec2 = Vec2(), size: Vec2 = Vec2()):
        self.id = _global_id()
        self.name = name or self._generate_name()
        self.children = []
        self.position = position
        self.size = size

    def _generate_name(self) -> str:
        return type(self).__class__.__name__ + '_' + str(self.id)

    def add_child(self, *nodes: 'Node') -> 'Node':
        self.children.extend(nodes)
        return self

    def get_adjusted_rect(self, offset: Vec2) -> SimpleRect:
        return (
            self.position.x - self.size.x / 2 + offset.x,
            self.position.y - self.size.y / 2 + offset.y,
            self.size.x,
            self.size.y,
        )

    def update(self, game: 'Game') -> None:
        pass

    def draw(self, surface: pygame.Surface, offset: Vec2) -> None:
        pass

    def __str__(self):
        return self.name


class RectNode(Node):
    color: int

    def __init__(
            self,
            name: str = '',
            position: Vec2 = Vec2(),
            size: Vec2 = Vec2(100, 100),
            color: int = 0xFFFFFF,
    ):
        super().__init__(name, position, size)
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

    def update(self, game: 'Game') -> None:
        def update_inner(node: Node) -> None:
            for child_node in node.children:
                update_inner(child_node)

            node.update(game)

        update_inner(self.root_node)

    def draw(self, surface: pygame.Surface) -> None:
        def draw_inner(node: Node, offset: Vec2) -> None:
            node.draw(surface, offset)
            for child_node in node.children:
                draw_inner(child_node, offset + node.position)

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
    screen_surface: pygame.Surface
    clock: pygame.time.Clock
    target_fps: int
    clear_color: int
    scene_graph: SceneGraph

    def __init__(self, config: EngineConfig):
        pygame.init()
        pygame.mixer.init()

        self.screen_surface = pygame.display.set_mode((config.width, config.height), pygame.RESIZABLE | pygame.SCALED)
        self.clock = pygame.time.Clock()
        self.target_fps = config.target_fps
        self.clear_color = config.clear_color
        self.scene_graph = SceneGraph()

        self.set_title(config.title)

    def _shutdown(self) -> None:
        pygame.quit()

    def set_title(self, title: str) -> None:
        pygame.display.set_caption(title)

    def get_fps(self) -> float:
        return self.clock.get_fps()

    def get_spf(self) -> float:
        return 1.0 / self.clock.get_fps()

    def _handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        return True

    def run(self, game: Game) -> None:
        game.engine = self
        game.scene_graph = self.scene_graph
        game.on_start()

        while True:
            if not self._handle_events():
                game.on_stop()
                self._shutdown()
                break

            game.dt = self.clock.tick(self.target_fps) / 1000.0

            self.screen_surface.fill(self.clear_color)

            self.scene_graph.update(game)
            self.scene_graph.draw(self.screen_surface)

            game.overdraw(self.screen_surface)

            pygame.display.flip()


def run_game(game: Game) -> None:
    _Engine(game.get_config()).run(game)
