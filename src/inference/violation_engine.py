import cv2
import numpy as np
from typing import Optional
from dataclasses import dataclass

from src.config import load_config, load_violation_rules
from src.inference.detector import HelmetDetector
from src.inference.tracker import Tracker
from src.inference.helmet_violation import HelmetViolationDetector
from src.inference.evidence import EvidenceGenerator


@dataclass
class ViolationResult:
    violation_id: str
    violation_type: str
    track_id: int
    confidence: float
    fine_amount: int
    evidence: Optional[dict] = None


class ViolationEngine:
    def __init__(self, config: dict = None):
        self.config = config or load_config()
        inference_cfg = self.config

        self.helmet_detector = HelmetDetector(self.config)
        self.tracker = Tracker()

        self.helmet_violation = HelmetViolationDetector(
            confirmation_frames=inference_cfg.get("helmet_confirmation_frames", 3)
        )

        self.evidence_gen = EvidenceGenerator(config=self.config)

        self.rules = load_violation_rules().get("rules", {})
        self.frame_skip = max(1, 30 // inference_cfg.get("inference_fps", 10))
        self._frame_count = 0
        self._confidence_threshold = inference_cfg.get("confidence_threshold", 0.45)
        self._last_detections = []

    @property
    def confidence_threshold(self):
        return self._confidence_threshold

    @confidence_threshold.setter
    def confidence_threshold(self, value: float):
        self._confidence_threshold = value
        self.helmet_detector.settings["confidence_threshold"] = value

    def process_frame(self, frame: np.ndarray, camera_id: str = "CAM_01") -> list:
        self._frame_count += 1
        if self._frame_count % self.frame_skip != 0:
            return []

        violations = []

        helmet_detections = self.helmet_detector.detect_helmets(frame)
        tracked_objects = self.tracker.update(helmet_detections, frame)

        for obj in tracked_objects:
            obj["frame_w"] = frame.shape[1]
            obj["frame_h"] = frame.shape[0]

        self._last_detections = tracked_objects

        helmet_violations = self.helmet_violation.process_frame(
            frame, tracked_objects, helmet_detections
        )
        for v in helmet_violations:
            violations.append(self._handle_violation(v, frame, camera_id))

        return violations

    def _handle_violation(self, candidate, frame: np.ndarray, camera_id: str) -> ViolationResult:
        rule = self.rules.get(candidate.violation_type, {})
        fine_amount = rule.get("fine_amount", 1000)

        evidence = self.evidence_gen.generate(
            frame=frame,
            violation_type=candidate.violation_type,
            track_id=candidate.track_id,
            bbox=candidate.bbox,
            plate_number=None,
            confidence=candidate.best_confidence,
            camera_id=camera_id,
        )

        return ViolationResult(
            violation_id=evidence["violation_id"] if evidence else "unknown",
            violation_type=candidate.violation_type,
            track_id=candidate.track_id,
            confidence=candidate.best_confidence,
            fine_amount=fine_amount,
            evidence=evidence,
        )

    def reset(self):
        self.tracker.reset()
        self.helmet_violation.reset()
        self._frame_count = 0
        self._last_detections = []

    def get_last_detections(self) -> list:
        return self._last_detections

    def process_image(self, image_path: str, camera_id: str = "CAM_01") -> list:
        frame = cv2.imread(image_path)
        if frame is None:
            raise ValueError(f"Could not read image: {image_path}")
        self.reset()
        self._frame_count = 0
        saved_skip = self.frame_skip
        self.frame_skip = 1
        violations = self.process_frame(frame, camera_id)
        self.frame_skip = saved_skip
        return violations

    def process_video(
        self,
        video_path: str,
        camera_id: str = "CAM_01",
        max_frames: int = None,
    ) -> list:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        all_violations = []
        self.reset()
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if max_frames and frame_idx >= max_frames:
                break

            violations = self.process_frame(frame, camera_id)
            all_violations.extend(violations)
            frame_idx += 1

        cap.release()
        return all_violations
