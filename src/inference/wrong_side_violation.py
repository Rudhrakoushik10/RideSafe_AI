import cv2
import numpy as np
import math
from typing import Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class WrongSideViolationCandidate:
    track_id: int
    violation_type: str = "WRONG_SIDE"
    frame_count: int = 0
    confirmed: bool = False
    best_frame: Optional[np.ndarray] = None
    best_confidence: float = 0.0
    bbox: Optional[list] = None
    plate_number: Optional[str] = None
    wrong_frames: int = 0


class WrongSideViolationDetector:
    def __init__(
        self,
        confirmation_frames: int = 5,
        angle_threshold: float = 150.0,
        road_direction: Optional[list] = None,
    ):
        self.confirmation_frames = confirmation_frames
        self.angle_threshold = angle_threshold
        self.road_direction = road_direction  # [dx, dy] normalized
        self.candidates = {}
        self.track_directions = defaultdict(list)

    def configure(self, road_direction: list):
        norm = math.sqrt(road_direction[0]**2 + road_direction[1]**2)
        if norm > 0:
            self.road_direction = [road_direction[0] / norm, road_direction[1] / norm]

    def _compute_direction_angle(self, movement: tuple) -> float:
        if self.road_direction is None:
            return 0.0
        dx, dy = movement
        norm = math.sqrt(dx**2 + dy**2)
        if norm < 1.0:
            return 0.0
        dx_norm = dx / norm
        dy_norm = dy / norm
        dot = dx_norm * self.road_direction[0] + dy_norm * self.road_direction[1]
        dot = max(-1.0, min(1.0, dot))
        angle = math.degrees(math.acos(dot))
        return angle

    def _is_wrong_side(self, track_id: int, movement: tuple) -> bool:
        angle = self._compute_direction_angle(movement)
        self.track_directions[track_id].append(angle)
        if len(self.track_directions[track_id]) > 30:
            self.track_directions[track_id].pop(0)

        recent_angles = self.track_directions[track_id][-5:]
        if len(recent_angles) < 3:
            return False
        avg_angle = sum(recent_angles) / len(recent_angles)
        return avg_angle > self.angle_threshold

    def process_frame(
        self,
        frame: np.ndarray,
        tracked_objects: list,
        tracker,
    ) -> list:
        violations = []
        current_track_ids = set()

        for obj in tracked_objects:
            track_id = obj["track_id"]
            bbox = obj["bbox"]
            current_track_ids.add(track_id)

            direction = tracker.get_direction(track_id)
            if direction is None:
                continue

            if self._is_wrong_side(track_id, direction):
                if track_id in self.candidates:
                    candidate = self.candidates[track_id]
                    candidate.frame_count += 1
                    candidate.wrong_frames += 1
                    candidate.bbox = bbox
                    self._update_best_frame(candidate, frame, bbox)
                    if candidate.wrong_frames >= self.confirmation_frames:
                        candidate.confirmed = True
                        violations.append(candidate)
                else:
                    candidate = WrongSideViolationCandidate(
                        track_id=track_id,
                        frame_count=1,
                        wrong_frames=1,
                        bbox=bbox,
                    )
                    self._update_best_frame(candidate, frame, bbox)
                    self.candidates[track_id] = candidate
            else:
                if track_id in self.candidates:
                    candidate = self.candidates[track_id]
                    candidate.wrong_frames = max(0, candidate.wrong_frames - 1)
                    if candidate.wrong_frames == 0:
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
        self.track_directions.clear()
