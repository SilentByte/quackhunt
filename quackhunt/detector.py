#
# QUACK HUNT
# Copyright (c) 2023 SilentByte <https://silentbyte.com/>
#


from dataclasses import dataclass

import cv2
import numpy as np

Point = tuple[float, float]
Size = tuple[int, int]
Rect = tuple[int, int, int]
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
    ):
        self.video_capture = cv2.VideoCapture(video_capture_index)
        self.flip_vertically = flip_vertically
        self.flip_horizontally = flip_horizontally
        self.show_debug_windows = show_debug_windows

        self.primary_lower_threshold = np.array(primary_lower_threshold)
        self.primary_upper_threshold = np.array(primary_upper_threshold)
        self.primary_min_confidence = primary_min_confidence

        self.secondary_lower_threshold = np.array(secondary_lower_threshold)
        self.secondary_upper_threshold = np.array(secondary_upper_threshold)
        self.secondary_min_confidence = secondary_min_confidence

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

    @staticmethod
    def _convert_rect_to_position(rect: Rect | None, frame_size: Size) -> Point | None:
        if rect is None:
            return None

        center = (rect[0] + rect[2] / 2, rect[1] + rect[3] / 2)
        return (
            center[0] / frame_size[0],
            center[1] / frame_size[1],
        )

    def process_frame(self) -> DetectionResult:
        if self.video_capture is None:
            raise DetectorException('Video capture is not initialized')

        result, frame = self.video_capture.read()
        if not result:
            return DetectionResult()

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
            primary_detection=Detector._convert_rect_to_position(primary_detection, frame_size),
            secondary_detection=Detector._convert_rect_to_position(secondary_detection, frame_size),
        )

    def destroy(self) -> None:
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None

        if self.show_debug_windows:
            cv2.destroyAllWindows()
