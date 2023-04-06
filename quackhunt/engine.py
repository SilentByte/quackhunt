#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#

from time import time
from dataclasses import dataclass
from typing import List, Any, Union

import pygame as pyg

from quackhunt import utils


def _global_id() -> int:
    _global_id.counter += 1
    return _global_id.counter


_global_id.counter = 0


@dataclass
class EngineConfig:
    title: str = 'Quack Hunt Engine'
    width: int = 1920
    height: int = 1080
    vsync: bool = True
    target_fps: int = 60
    clear_color: int = 0x111111
    sound_channels: int = 64


Vec2 = pyg.Vector2
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

    def find_child(self, name: str) -> Union['Node', Any]:
        def find_direct_child(node: Node, child_name: str):
            for child_node in node.children:
                if child_node.name == child_name:
                    return child_node

            return None

        current_node = self
        for name_segment in name.split('/'):
            current_node = find_direct_child(current_node, name_segment)
            if current_node is None:
                raise ValueError(f'Node {name} is not a child of {self.name}')

        return current_node

    def get_adjusted_rect(self, offset: Vec2) -> SimpleRect:
        return (
            self.position.x - self.size.x / 2 + offset.x,
            self.position.y - self.size.y / 2 + offset.y,
            self.size.x,
            self.size.y,
        )

    def update(self, game: 'Game') -> None:
        pass

    def draw(self, surface: pyg.Surface, offset: Vec2) -> None:
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

    def draw(self, surface: pyg.Surface, offset: Vec2) -> None:
        pyg.draw.rect(surface, self.color, self.get_adjusted_rect(offset))


class SpriteNode(Node):
    texture: pyg.Surface

    def __init__(
            self,
            filename: str,
            name: str = '',
            position: Vec2 = Vec2(),
    ):
        self.texture = pyg.image.load(filename).convert_alpha()
        super().__init__(name, position, Vec2(self.texture.get_width(), self.texture.get_height()))

    def draw(self, surface: pyg.Surface, offset: Vec2) -> None:
        surface.blit(self.texture, self.get_adjusted_rect(offset))


class SoundNode(Node):
    sound: pyg.mixer.Sound

    def __init__(
            self,
            filename: str,
            name: str = '',
    ):
        self.sound = pyg.mixer.Sound(filename)
        super().__init__(name)

    def play(self) -> None:
        channel = pyg.mixer.find_channel(True)
        channel.play(self.sound)


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

    def draw(self, surface: pyg.Surface) -> None:
        def draw_inner(node: Node, offset: Vec2) -> None:
            node.draw(surface, offset)
            for child_node in node.children:
                draw_inner(child_node, offset + node.position)

        draw_inner(self.root_node, self.root_node.position)


# noinspection PyMethodMayBeStatic
class Game:
    pyg = pyg
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

    def on_frame_start(self) -> None:
        pass

    def on_frame_end(self) -> None:
        pass


# noinspection PyMethodMayBeStatic
class _Engine:
    screen_surface: pyg.Surface
    clock: pyg.time.Clock
    target_fps: int
    clear_color: int
    scene_graph: SceneGraph
    frame_counter: int
    start_time: float

    def __init__(self, config: EngineConfig):
        pyg.init()
        pyg.mixer.init()

        self.screen_surface = pyg.display.set_mode(
            size=(config.width, config.height),
            flags=pyg.RESIZABLE | pyg.SCALED,
            vsync=config.vsync,
        )

        self.clock = pyg.time.Clock()
        self.target_fps = config.target_fps
        self.clear_color = config.clear_color
        self.scene_graph = SceneGraph()
        self.fps = 0.0
        self.frame_counter = 0
        self.start_time = 0

        pyg.mixer.set_num_channels(config.sound_channels)

        self.set_title(config.title)

    def _shutdown(self) -> None:
        pyg.quit()

    def set_title(self, title: str) -> None:
        pyg.display.set_caption(title)

    def get_time(self) -> float:
        return time() - self.start_time

    def log(self, object) -> None:
        utils.debug_print(object, f'{self.frame_counter}   {self.get_time():.2f}   {self.clock.get_fps():.0f}  ')

    def _handle_events(self) -> bool:
        for event in pyg.event.get():
            if event.type == pyg.QUIT:
                return False

        return True

    def run(self, game: Game) -> None:
        self.start_time = time()

        game.pyg = pyg
        game.engine = self
        game.scene_graph = self.scene_graph
        game.on_start()

        while True:
            self.frame_counter += 1

            if not self._handle_events():
                game.on_stop()
                self._shutdown()
                break

            game.dt = self.clock.tick(self.target_fps) / 1000.0

            self.screen_surface.fill(self.clear_color)

            game.on_frame_start()
            self.scene_graph.update(game)
            self.scene_graph.draw(self.screen_surface)
            game.on_frame_end()

            pyg.display.flip()


def run_game(game: Game) -> None:
    _Engine(game.get_config()).run(game)
