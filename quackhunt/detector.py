#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#

import threading
from dataclasses import dataclass

import cv2
import numpy as np
import tkinter as tk

from quackhunt import config

Point = tuple[float, float]
Size = tuple[int, int]
Rect = tuple[int, int, int, int]
Color = tuple[int, int, int]


class DetectorException(Exception):
    pass


@dataclass
class DetectionResult:
    primary_detection: Point = None
    secondary_detection: Point = None


class Detector:
    def __init__(
            self,
            video_capture_index: int = 0,
            flip_vertically: bool = False,
            flip_horizontally: bool = False,
            show_debug_windows: bool = False,
            primary_lower_threshold: Color = (55, 20, 20),
            primary_upper_threshold: Color = (70, 255, 255),
            primary_min_confidence: float = 0.001,
            secondary_lower_threshold: Color = (110, 100, 20),
            secondary_upper_threshold: Color = (126, 240, 240),
            secondary_min_confidence: float = 0.001,
            stretch_factors: Point = (1.0, 1.0),
            nudge_addends: Point = (0.0, 0.0),
    ):
        self.is_destroyed = False
        self.video_capture = cv2.VideoCapture(video_capture_index)
        self.current_frame = None

        self.capture_thread = threading.Thread(target=self._threaded_frame_reader)
        self.capture_thread.daemon = True
        self.capture_thread.start()

        self.flip_vertically = flip_vertically
        self.flip_horizontally = flip_horizontally
        self.show_debug_windows = show_debug_windows

        self.primary_lower_threshold = np.array(primary_lower_threshold)
        self.primary_upper_threshold = np.array(primary_upper_threshold)
        self.primary_min_confidence = primary_min_confidence

        self.secondary_lower_threshold = np.array(secondary_lower_threshold)
        self.secondary_upper_threshold = np.array(secondary_upper_threshold)
        self.secondary_min_confidence = secondary_min_confidence

        self.stretch_factors = stretch_factors
        self.nudge_addends = nudge_addends

    def _threaded_frame_reader(self):
        while not self.is_destroyed:
            result, frame = self.video_capture.read()

            if result:
                self.current_frame = frame

    @staticmethod
    def _detect(mask, frame_size: Size, min_confidence: float):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        largest_contour = max(contours, key=cv2.contourArea)
        confidence = cv2.contourArea(largest_contour) / (frame_size[0] * frame_size[1])

        if confidence < min_confidence:
            return None

        return cv2.boundingRect(largest_contour)

    @staticmethod
    def _annotate_detection(frame, detection: Rect, color: Color):
        cv2.rectangle(
            frame,
            (detection[0], detection[1]),
            (detection[0] + detection[2], detection[1] + detection[3]),
            color,
            2,
        )

        cv2.circle(
            frame,
            (int(detection[0] + detection[2] / 2), int(detection[1] + detection[3] / 2)),
            5,
            color,
            -1,
        )

    def _annotate_adjusted_detection(self, frame, detection: Rect, frame_size: Size, color: Color):
        position = self._convert_rect_to_position(detection, frame_size)
        if position is None:
            return

        x = int((position[0] / 2 + 0.5) * frame_size[0])
        y = int((position[1] / 2 + 0.5) * frame_size[1])

        cv2.line(
            frame,
            (int(frame_size[0] / 2), 0),
            (int(frame_size[0] / 2), int(frame_size[1])),
            (255, 0, 255),
        )

        cv2.line(
            frame,
            (0, int(frame_size[1] / 2)),
            (int(frame_size[0]), int(frame_size[1] / 2)),
            (255, 0, 255),
        )

        cv2.line(
            frame,
            (x, 0),
            (x, frame_size[1]),
            color,
        )

        cv2.line(
            frame,
            (0, y),
            (frame_size[0], y),
            color,
        )

    def _convert_rect_to_position(self, rect: Rect | None, frame_size: Size) -> Point | None:
        if rect is None:
            return None

        center = (rect[0] + rect[2] / 2, rect[1] + rect[3] / 2)
        return (
            (center[0] / frame_size[0] - 0.5) * 2 * self.stretch_factors[0] + self.nudge_addends[0],
            (center[1] / frame_size[1] - 0.5) * 2 * self.stretch_factors[1] + self.nudge_addends[1],
        )

    def process_frame(self) -> DetectionResult:
        if self.is_destroyed:
            raise DetectorException('Detector has already been destroyed')

        if self.video_capture is None:
            raise DetectorException('Video capture is not initialized')

        if self.current_frame is None:
            return DetectionResult()

        frame = self.current_frame

        if self.flip_vertically:
            frame = cv2.flip(frame, 0)

        if self.flip_horizontally:
            frame = cv2.flip(frame, 1)

        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        primary_mask = cv2.inRange(hsv_frame, self.primary_lower_threshold, self.primary_upper_threshold)
        secondary_mask = cv2.inRange(hsv_frame, self.secondary_lower_threshold, self.secondary_upper_threshold)

        frame_size = (frame.shape[1], frame.shape[0])

        primary_detection = Detector._detect(primary_mask, frame_size, self.primary_min_confidence)
        secondary_detection = Detector._detect(secondary_mask, frame_size, self.secondary_min_confidence)

        if primary_detection is not None:
            Detector._annotate_detection(frame, primary_detection, (0, 255, 0))
            self._annotate_adjusted_detection(frame, primary_detection, frame_size, (0, 255, 0))

        if secondary_detection is not None:
            Detector._annotate_detection(frame, secondary_detection, (255, 0, 0))

        combined_frames = np.hstack((
            frame,
            cv2.cvtColor(primary_mask, cv2.COLOR_GRAY2BGR),
            cv2.cvtColor(secondary_mask, cv2.COLOR_GRAY2BGR),
        ))

        if self.show_debug_windows:
            cv2.imshow('combined_frames', combined_frames)
            cv2.pollKey()

        return DetectionResult(
            primary_detection=self._convert_rect_to_position(primary_detection, frame_size),
            secondary_detection=self._convert_rect_to_position(secondary_detection, frame_size),
        )

    def destroy(self) -> None:
        self.is_destroyed = True

        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None

        if self.show_debug_windows:
            cv2.destroyAllWindows()


def calibration_tool_main():
    config_data = config.load_config()
    detector = Detector(
        video_capture_index=config_data.video_capture_index,
        flip_vertically=config_data.flip_vertically,
        flip_horizontally=config_data.flip_horizontally,
        show_debug_windows=True,
        primary_lower_threshold=config_data.primary_lower_threshold,
        primary_upper_threshold=config_data.primary_upper_threshold,
        primary_min_confidence=config_data.primary_min_confidence,
        secondary_lower_threshold=config_data.secondary_lower_threshold,
        secondary_upper_threshold=config_data.secondary_upper_threshold,
        secondary_min_confidence=config_data.secondary_min_confidence,
        stretch_factors=config_data.stretch_factors,
        nudge_addends=config_data.nudge_addends,
    )

    def primary_lower_threshold_h_callback(value: str):
        detector.primary_lower_threshold[0] = int(value)

    def primary_lower_threshold_s_callback(value: str):
        detector.primary_lower_threshold[1] = int(value)

    def primary_lower_threshold_v_callback(value: str):
        detector.primary_lower_threshold[2] = int(value)

    def primary_upper_threshold_h_callback(value: str):
        detector.primary_upper_threshold[0] = int(value)

    def primary_upper_threshold_s_callback(value: str):
        detector.primary_upper_threshold[1] = int(value)

    def primary_upper_threshold_v_callback(value: str):
        detector.primary_upper_threshold[2] = int(value)

    def primary_min_confidence_callback(value: str):
        detector.primary_min_confidence = ((100 ** (float(value) / 10000)) - 1) / 99

    def secondary_lower_threshold_h_callback(value: str):
        detector.secondary_lower_threshold[0] = int(value)

    def secondary_lower_threshold_s_callback(value: str):
        detector.secondary_lower_threshold[1] = int(value)

    def secondary_lower_threshold_v_callback(value: str):
        detector.secondary_lower_threshold[2] = int(value)

    def secondary_upper_threshold_h_callback(value: str):
        detector.secondary_upper_threshold[0] = int(value)

    def secondary_upper_threshold_s_callback(value: str):
        detector.secondary_upper_threshold[1] = int(value)

    def secondary_upper_threshold_v_callback(value: str):
        detector.secondary_upper_threshold[2] = int(value)

    def secondary_min_confidence_callback(value: str):
        detector.secondary_min_confidence = ((100 ** (float(value) / 10000)) - 1) / 99

    def stretch_factor_h_callback(value: str):
        detector.stretch_factors = (float(value) / 10000 + 1, detector.stretch_factors[1])

    def stretch_factor_v_callback(value: str):
        detector.stretch_factors = (detector.stretch_factors[0], float(value) / 10000 + 1)

    def nudge_addend_h_callback(value: str):
        detector.nudge_addends = (float(value) / 5000 - 1, detector.nudge_addends[1])

    def nudge_addend_v_callback(value: str):
        detector.nudge_addends = (detector.nudge_addends[0], float(value) / 5000 - 1)

    def save_config_callback():
        config_data.flip_vertically = detector.flip_vertically
        config_data.flip_horizontally = detector.flip_horizontally

        config_data.primary_lower_threshold = list(int(x) for x in detector.primary_lower_threshold)
        config_data.primary_upper_threshold = list(int(x) for x in detector.primary_upper_threshold)
        config_data.primary_min_confidence = detector.primary_min_confidence

        config_data.secondary_lower_threshold = list(int(x) for x in detector.secondary_lower_threshold)
        config_data.secondary_upper_threshold = list(int(x) for x in detector.secondary_upper_threshold)
        config_data.secondary_min_confidence = detector.secondary_min_confidence

        config_data.stretch_factors = list(float(x) for x in detector.stretch_factors)
        config_data.nudge_addends = list(float(x) for x in detector.nudge_addends)

        config.save_config(config_data)

    def label(text: str):
        tk.Label(root, text=text) \
            .pack(side=tk.TOP, padx=10, pady=10)

    def slider(min: int, max: int, value: int, callback: callable):
        scale = tk.Scale(root, from_=min, to=max, orient=tk.HORIZONTAL, length=400, command=callback)
        scale.set(value)
        scale.pack(side=tk.TOP, fill=tk.X, padx=50, pady=10)

    def button(text: str, callback: callable):
        tk.Button(text=text, height=2, command=callback) \
            .pack(side=tk.TOP, fill=tk.X, padx=50, pady=10)

    root = tk.Tk()
    root.title('QuackHunt Calibration')
    root.geometry('1200x2220')

    calibration_tool_main.is_running = True

    def terminate():
        calibration_tool_main.is_running = False

    root.protocol('WM_DELETE_WINDOW', terminate)

    label(
        '\n'
        'QUACK HUNT CALIBRATION\n'
        '\n'
        'Hold objects of two distinct colors into the camera (primary/secondary)\n'
        'and adjust sliders until they are detected correctly.\n'
        '\n'
    )

    label('primary_lower_threshold (HSV)')
    slider(0, 255, config_data.primary_lower_threshold[0], primary_lower_threshold_h_callback)
    slider(0, 255, config_data.primary_lower_threshold[1], primary_lower_threshold_s_callback)
    slider(0, 255, config_data.primary_lower_threshold[2], primary_lower_threshold_v_callback)

    label('primary_upper_threshold (HSV)')
    slider(0, 255, config_data.primary_upper_threshold[0], primary_upper_threshold_h_callback)
    slider(0, 255, config_data.primary_upper_threshold[1], primary_upper_threshold_s_callback)
    slider(0, 255, config_data.primary_upper_threshold[2], primary_upper_threshold_v_callback)

    label('primary_min_confidence')
    slider(0, 10000, int(config_data.primary_min_confidence * 10000), primary_min_confidence_callback)

    label('secondary_lower_threshold (HSV)')
    slider(0, 255, config_data.secondary_lower_threshold[0], secondary_lower_threshold_h_callback)
    slider(0, 255, config_data.secondary_lower_threshold[1], secondary_lower_threshold_s_callback)
    slider(0, 255, config_data.secondary_lower_threshold[2], secondary_lower_threshold_v_callback)

    label('secondary_upper_threshold (HSV)')
    slider(0, 255, config_data.secondary_upper_threshold[0], secondary_upper_threshold_h_callback)
    slider(0, 255, config_data.secondary_upper_threshold[1], secondary_upper_threshold_s_callback)
    slider(0, 255, config_data.secondary_upper_threshold[2], secondary_upper_threshold_v_callback)

    label('secondary_min_confidence')
    slider(0, 10000, int(config_data.secondary_min_confidence * 10000), secondary_min_confidence_callback)

    label('stretch_factors (horizontal/vertical)')
    slider(0, 10000, int((config_data.stretch_factors[0] - 1) * 10000), stretch_factor_h_callback)
    slider(0, 10000, int((config_data.stretch_factors[1] - 1) * 10000), stretch_factor_v_callback)

    label('nudge_addends (horizontal/vertical)')
    slider(0, 10000, int((config_data.nudge_addends[0] + 1) * 5000), nudge_addend_h_callback)
    slider(0, 10000, int((config_data.nudge_addends[1] + 1) * 5000), nudge_addend_v_callback)

    button('SAVE CONFIG', save_config_callback)

    while calibration_tool_main.is_running:
        root.update()
        detector.process_frame()

    detector.destroy()
    root.destroy()


calibration_tool_main.is_running = False
