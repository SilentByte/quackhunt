#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#

from time import time
from dataclasses import dataclass
from typing import List, Any, Union, Optional

import pygame as pyg

from quackhunt import utils


def _global_id() -> int:
    _global_id.counter += 1
    return _global_id.counter


_global_id.counter = 0


class DirectDict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


@dataclass
class EngineConfig:
    title: str = 'Quack Hunt Engine'
    width: int = 1920
    height: int = 1080
    vsync: bool = True
    target_fps: int = 60
    clear_color: int = 0x111111
    sound_channels: int = 64
    show_cursor: bool = True


Vec2 = pyg.Vector2
SimpleRect = tuple[int | float, int | float, int | float, int | float]


class Node:
    id: int
    name: str
    parent: Optional['Node']
    children: List['Node']
    position: Vec2
    size: Vec2
    visible: bool

    def __init__(self, name: str = '', position: Vec2 = None, size: Vec2 = None):
        self.id = _global_id()
        self.name = name or self._generate_name()
        self.parent = None
        self.children = []
        self.position = position or Vec2()
        self.size = size or Vec2()
        self.visible = True

    def _generate_name(self) -> str:
        return self.__class__.__name__ + '_' + str(self.id)

    def add_child(self, *nodes: 'Node') -> 'Node':
        for node in nodes:
            node.parent = self
            self.children.append(node)

        return self

    def remove_all_children(self) -> None:
        for child in self.children:
            child.parent = None

        self.children.clear()

    def remove(self) -> None:
        self.parent.children.remove(self)
        self.parent = None

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
        self.texture = load_texture(filename)
        super().__init__(name, position, Vec2(self.texture.get_width(), self.texture.get_height()))

    def draw(self, surface: pyg.Surface, offset: Vec2) -> None:
        surface.blit(self.texture, self.get_adjusted_rect(offset))


class TextNode(Node):
    font: pyg.font.Font
    text: str
    color: int

    def __init__(
            self,
            font_name: str | None,
            font_size: int,
            name: str = '',
            position: Vec2 = Vec2(),
            text: str = '',
            color: int = 0xFFFFFFFF,
    ):
        super().__init__(name, position)

        self.font = pyg.font.Font(font_name or None, font_size)
        self.text = text
        self.color = color

    def draw(self, surface: pyg.Surface, offset: Vec2) -> None:
        text_surface = self.font.render(self.text, True, self.color)
        surface.blit(text_surface, self.position)


class SoundNode(Node):
    sound: pyg.mixer.Sound

    def __init__(
            self,
            filename: str,
            name: str = '',
    ):
        self.sound = load_sound(filename)
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
            if node.visible:
                node.draw(surface, offset)

                for child_node in node.children:
                    draw_inner(child_node, offset + node.position)

        draw_inner(self.root_node, self.root_node.position)


EventQueue = List[tuple[str, Any]]
TimerQueue = List[tuple[float, callable, dict]]

TEXTURE_CACHE: dict[str, pyg.Surface] = {}
SOUND_CACHE: dict[str, pyg.mixer.Sound] = {}


def load_texture(filename: str) -> pyg.Surface:
    surface = TEXTURE_CACHE.get(filename, None)

    if surface is not None:
        return surface

    surface = pyg.image.load(filename).convert_alpha()
    TEXTURE_CACHE[filename] = surface

    return surface


def load_sound(filename: str) -> pyg.mixer.Sound:
    sound = SOUND_CACHE.get(filename, None)

    if sound is not None:
        return sound

    sound = pyg.mixer.Sound(filename)
    SOUND_CACHE[filename] = sound

    return sound


# noinspection PyMethodMayBeStatic
class Game:
    pyg = pyg
    engine: '_Engine' = None
    scene_graph: SceneGraph = None
    native_events: List[pyg.event.Event] = None
    events: EventQueue = None
    dt: float = 0
    is_running: bool = False

    def get_config(self) -> EngineConfig:
        return EngineConfig(
            title='Game',
            width=1920,
            height=1080,
            target_fps=60,
            clear_color=0x111111,
        )

    def on_started(self) -> None:
        pass

    def on_stopped(self) -> None:
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
    event_queue: EventQueue
    timer_queue: TimerQueue

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
        self.event_queue = []
        self.timer_queue = []

        pyg.mouse.set_visible(config.show_cursor)
        pyg.mixer.set_num_channels(config.sound_channels)

        self.set_title(config.title)

    def _shutdown(self) -> None:
        pyg.quit()

    def set_title(self, title: str) -> None:
        pyg.display.set_caption(title)

    def get_time(self) -> float:
        return time() - self.start_time

    def log(self, message: str, object=None) -> None:
        utils.debug_print(
            object,
            f'{self.frame_counter}   {self.get_time():.2f}   {self.clock.get_fps():.0f}  {message}',
        )

    def queue_event(self, name: str, **kwargs) -> None:
        data = DirectDict(kwargs)
        self.log('Event queued', (name, data))
        self.event_queue.append((name, data))

    def queue_timer_event(self, delay: float, callback: callable, **kwargs) -> None:
        self.log('Timer event queued', (delay, callback.__name__, kwargs))
        self.timer_queue.append(
            (pyg.time.get_ticks() + delay * 1000, callback, kwargs)
        )

    def _process_timers(self) -> None:
        keep = []
        for timer in self.timer_queue:
            if timer[0] <= pyg.time.get_ticks():
                timer[1](**timer[2])
            else:
                keep.append(timer)

        self.timer_queue = keep

    def _handle_native_events(self, game: Game) -> bool:
        game.native_events = pyg.event.get()

        for event in game.native_events:
            if event.type == pyg.QUIT:
                return False

            if event.type == pyg.KEYDOWN and event.key == pyg.K_ESCAPE:
                return False

        return True

    def run(self, game: Game) -> None:
        self.start_time = time()

        game.pyg = pyg
        game.engine = self
        game.scene_graph = self.scene_graph
        game.native_events = []
        game.dt = 0
        game.is_running = True

        game.on_started()

        while True:
            self.frame_counter += 1

            if not self._handle_native_events(game):
                game.is_running = False
                game.on_stopped()
                self._shutdown()
                break

            game.dt = self.clock.tick(self.target_fps) / 1000.0
            game.events = self.event_queue
            self.event_queue = []

            self.screen_surface.fill(self.clear_color)

            game.on_frame_start()
            self.scene_graph.update(game)
            self._process_timers()
            self.scene_graph.draw(self.screen_surface)
            game.on_frame_end()

            pyg.display.flip()


def run_game(game: Game) -> None:
    _Engine(game.get_config()).run(game)
