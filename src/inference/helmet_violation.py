import cv2
import numpy as np
from typing import Optional
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class ViolationCandidate:
    track_id: int
    violation_type: str
    frame_count: int = 0
    confirmed: bool = False
    best_frame: Optional[np.ndarray] = None
    best_confidence: float = 0.0
    bbox: Optional[list] = None
    plate_number: Optional[str] = None


class HelmetViolationDetector:
    def __init__(self, confirmation_frames: int = 3):
        self.confirmation_frames = confirmation_frames
        self.candidates = {}  # track_id -> ViolationCandidate

    def process_frame(
        self,
        frame: np.ndarray,
        tracked_objects: list,
        helmet_detections: list,
    ) -> list:
        violations = []
        current_track_ids = set()

        for obj in tracked_objects:
            track_id = obj["track_id"]
            bbox = obj["bbox"]
            current_track_ids.add(track_id)

            rider_roi = self._extract_rider_roi(frame, bbox)
            if rider_roi is None:
                continue

            has_helmet = self._check_helmet_in_roi(rider_roi, helmet_detections, bbox)

            if not has_helmet:
                if track_id in self.candidates:
                    candidate = self.candidates[track_id]
                    candidate.frame_count += 1
                    candidate.bbox = bbox
                    self._update_best_frame(candidate, frame, bbox)
                    if candidate.frame_count >= self.confirmation_frames:
                        candidate.confirmed = True
                        violations.append(candidate)
                else:
                    candidate = ViolationCandidate(
                        track_id=track_id,
                        violation_type="NO_HELMET",
                        frame_count=1,
                        bbox=bbox,
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

    def _extract_rider_roi(self, frame: np.ndarray, bbox: list) -> Optional[np.ndarray]:
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        x1 = max(0, min(x1, w))
        y1 = max(0, min(y1, h))
        x2 = max(0, min(x2, w))
        y2 = max(0, min(y2, h))
        if x2 <= x1 or y2 <= y1:
            return None
        roi_h = int((y2 - y1) * 0.6)
        rider_y1 = y1
        rider_y2 = y1 + roi_h
        return frame[rider_y1:rider_y2, x1:x2]

    def _check_helmet_in_roi(
        self, rider_roi: np.ndarray, helmet_detections: list, rider_bbox: list
    ) -> bool:
        rider_x1, rider_y1, rider_x2, rider_y2 = rider_bbox
        rider_h = rider_y2 - rider_y1
        head_region_y2 = rider_y1 + int(rider_h * 0.35)

        for det in helmet_detections:
            det_bbox = det["bbox"]
            det_cx = (det_bbox[0] + det_bbox[2]) / 2
            det_cy = (det_bbox[1] + det_bbox[3]) / 2

            if (rider_x1 <= det_cx <= rider_x2 and
                rider_y1 <= det_cy <= head_region_y2):
                if det["class_name"].lower() in ["helmet", "with_helmet", "helmet_on"]:
                    return True
                elif det["class_id"] == 0:
                    return True
        return False

    def _update_best_frame(self, candidate: ViolationCandidate, frame: np.ndarray, bbox: list):
        current_conf = 1.0 - (candidate.frame_count / (self.confirmation_frames * 2))
        if candidate.best_frame is None or current_conf > candidate.best_confidence:
            x1, y1, x2, y2 = bbox
            h, w = frame.shape[:2]
            pad = 20
            crop = frame[max(0, y1-pad):min(h, y2+pad), max(0, x1-pad):min(w, x2+pad)]
            if crop.size > 0:
                candidate.best_frame = crop.copy()
                candidate.best_confidence = current_conf

    def reset(self):
        self.candidates.clear()
