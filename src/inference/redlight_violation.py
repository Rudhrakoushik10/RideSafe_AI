import cv2
import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class RedLightViolationCandidate:
    track_id: int
    violation_type: str = "RED_LIGHT"
    frame_count: int = 0
    confirmed: bool = False
    best_frame: Optional[np.ndarray] = None
    best_confidence: float = 0.0
    bbox: Optional[list] = None
    plate_number: Optional[str] = None
    crossed_at_red: bool = False


class RedLightViolationDetector:
    def __init__(
        self,
        confirmation_frames: int = 3,
        stop_line: Optional[list] = None,
        traffic_light_roi: Optional[list] = None,
    ):
        self.confirmation_frames = confirmation_frames
        self.stop_line = stop_line  # [[x1, y1], [x2, y2]]
        self.traffic_light_roi = traffic_light_roi  # [x1, y1, x2, y2]
        self.candidates = {}
        self.light_state = "UNKNOWN"  # RED, YELLOW, GREEN, UNKNOWN
        self._red_light_start = None

    def configure(self, stop_line: list, traffic_light_roi: list):
        self.stop_line = stop_line
        self.traffic_light_roi = traffic_light_roi

    def update_light_state(self, frame: np.ndarray, light_detections: list):
        if self.traffic_light_roi is None:
            return

        roi_x1, roi_y1, roi_x2, roi_y2 = self.traffic_light_roi
        h, w = frame.shape[:2]
        roi_x1 = max(0, min(roi_x1, w))
        roi_y1 = max(0, min(roi_y1, h))
        roi_x2 = max(0, min(roi_x2, w))
        roi_y2 = max(0, min(roi_y2, h))

        roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
        if roi.size == 0:
            return

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV) if len(roi.shape) == 3 else None
        if hsv is None:
            return

        red_mask1 = cv2.inRange(hsv, np.array([0, 100, 100]), np.array([10, 255, 255]))
        red_mask2 = cv2.inRange(hsv, np.array([160, 100, 100]), np.array([180, 255, 255]))
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        green_mask = cv2.inRange(hsv, np.array([35, 100, 100]), np.array([85, 255, 255]))
        yellow_mask = cv2.inRange(hsv, np.array([15, 100, 100]), np.array([35, 255, 255]))

        red_ratio = np.sum(red_mask > 0) / red_mask.size
        green_ratio = np.sum(green_mask > 0) / green_mask.size
        yellow_ratio = np.sum(yellow_mask > 0) / yellow_mask.size

        threshold = 0.15
        if red_ratio > threshold and red_ratio > green_ratio and red_ratio > yellow_ratio:
            self.light_state = "RED"
        elif green_ratio > threshold and green_ratio > red_ratio:
            self.light_state = "GREEN"
        elif yellow_ratio > threshold:
            self.light_state = "YELLOW"
        else:
            pass  # keep previous state

    def _crosses_stop_line(self, bbox: list) -> bool:
        if self.stop_line is None:
            return False

        x1, y1, x2, y2 = bbox
        vehicle_bottom = y2
        vehicle_cx = (x1 + x2) / 2

        line_y = self.stop_line[0][1]
        line_x1 = self.stop_line[0][0]
        line_x2 = self.stop_line[1][0]

        if vehicle_bottom > line_y and line_x1 <= vehicle_cx <= line_x2:
            return True
        return False

    def process_frame(
        self,
        frame: np.ndarray,
        tracked_objects: list,
        light_detections: list = None,
    ) -> list:
        if light_detections:
            self.update_light_state(frame, light_detections)

        violations = []
        current_track_ids = set()

        for obj in tracked_objects:
            track_id = obj["track_id"]
            bbox = obj["bbox"]
            current_track_ids.add(track_id)

            if self.light_state == "RED" and self._crosses_stop_line(bbox):
                if track_id in self.candidates:
                    candidate = self.candidates[track_id]
                    candidate.frame_count += 1
                    candidate.bbox = bbox
                    candidate.crossed_at_red = True
                    self._update_best_frame(candidate, frame, bbox)
                    if candidate.frame_count >= self.confirmation_frames:
                        candidate.confirmed = True
                        violations.append(candidate)
                else:
                    candidate = RedLightViolationCandidate(
                        track_id=track_id,
                        frame_count=1,
                        bbox=bbox,
                        crossed_at_red=True,
                    )
                    self._update_best_frame(candidate, frame, bbox)
                    self.candidates[track_id] = candidate
            else:
                if track_id in self.candidates:
                    del self.candidates[track_id]

        expired = [tid for tid in self.candidates if tid not in current_track_ids]
        for tid in expired:
            del self.candidates[tid]

        return violations

    def _update_best_frame(self, candidate, frame, bbox):
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        pad = 20
        crop = frame[max(0, y1-pad):min(h, y2+pad), max(0, x1-pad):min(w, x2+pad)]
        if crop.size > 0:
            candidate.best_frame = crop.copy()

    def reset(self):
        self.candidates.clear()
        self.light_state = "UNKNOWN"
