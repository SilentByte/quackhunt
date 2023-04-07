#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#

import os
import json

import dataclasses


def _list_to_color(data: list) -> tuple[int, int, int]:
    return (
        int(data[0]),
        int(data[1]),
        int(data[2]),
    )


@dataclasses.dataclass
class QuackHuntConfig:
    video_capture_index: int = 0
    flip_vertically: bool = False
    flip_horizontally: bool = False
    show_debug_windows: bool = False
    primary_lower_threshold: tuple[int, int, int] = (55, 20, 20)
    primary_upper_threshold: tuple[int, int, int] = (70, 255, 255)
    primary_min_confidence: float = 0.0
    secondary_lower_threshold: tuple[int, int, int] = (110, 100, 20)
    secondary_upper_threshold: tuple[int, int, int] = (126, 240, 240)
    secondary_min_confidence: float = 0.0

    @staticmethod
    def from_dict(config: dict) -> 'QuackHuntConfig':
        return QuackHuntConfig(
            video_capture_index=int(config['video_capture_index']),
            flip_vertically=bool(config['flip_vertically']),
            flip_horizontally=bool(config['flip_horizontally']),
            show_debug_windows=bool(config['show_debug_windows']),
            primary_lower_threshold=_list_to_color(config['primary_lower_threshold']),
            primary_upper_threshold=_list_to_color(config['primary_upper_threshold']),
            primary_min_confidence=float(config['primary_min_confidence']),
            secondary_lower_threshold=_list_to_color(config['secondary_lower_threshold']),
            secondary_upper_threshold=_list_to_color(config['secondary_upper_threshold']),
            secondary_min_confidence=float(config['secondary_min_confidence']),
        )

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def _config_file_path() -> str:
    return os.path.join(os.getcwd(), 'quackhunt.json')


def load_config() -> QuackHuntConfig:
    path = _config_file_path()
    try:
        with open(path, 'rb') as fp:
            return QuackHuntConfig.from_dict(json.load(fp))
    except Exception as e:
        print(f'Failed to load {path}; falling back to default config: {e}')
        return QuackHuntConfig()


def save_config(config: QuackHuntConfig) -> None:
    filename = _config_file_path()
    with open(filename, 'w') as fp:
        return json.dump(config.to_dict(), fp,indent=2)
