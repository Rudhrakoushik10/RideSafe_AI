import cv2
import numpy as np
from typing import Optional
from dataclasses import dataclass, field

from src.config import load_config, load_camera_config, load_violation_rules
from src.inference.detector import HelmetDetector, PlateDetector, TrafficLightDetector
from src.inference.tracker import Tracker
from src.inference.helmet_violation import HelmetViolationDetector
from src.inference.redlight_violation import RedLightViolationDetector
from src.inference.wrong_side_violation import WrongSideViolationDetector
from src.inference.ocr import OCRReader
from src.inference.evidence import EvidenceGenerator


@dataclass
class ViolationResult:
    violation_id: str
    violation_type: str
    track_id: int
    plate_number: Optional[str]
    confidence: float
    fine_amount: int
    evidence: Optional[dict] = None


class ViolationEngine:
    def __init__(self, config: dict = None):
        self.config = config or load_config()
        inference_cfg = self.config

        self.helmet_detector = HelmetDetector(self.config)
        self.plate_detector = PlateDetector(self.config)
        self.traffic_light_detector = TrafficLightDetector(self.config)
        self.tracker = Tracker()

        self.helmet_violation = HelmetViolationDetector(
            confirmation_frames=inference_cfg.get("helmet_confirmation_frames", 3)
        )
        self.redlight_violation = RedLightViolationDetector(
            confirmation_frames=inference_cfg.get("red_light_confirmation_frames", 3)
        )
        self.wrong_side_violation = WrongSideViolationDetector(
            confirmation_frames=inference_cfg.get("wrong_side_confirmation_frames", 5),
            angle_threshold=inference_cfg.get("wrong_side_angle_threshold", 150),
        )

        self.ocr = OCRReader(
            confidence_threshold=inference_cfg.get("ocr_confidence_threshold", 0.6)
        )
        self.evidence_gen = EvidenceGenerator(config=self.config)

        self.rules = load_violation_rules().get("rules", {})
        self.frame_skip = max(1, 30 // inference_cfg.get("inference_fps", 10))
        self._frame_count = 0
        self._confidence_threshold = inference_cfg.get("confidence_threshold", 0.45)

    @property
    def confidence_threshold(self):
        return self._confidence_threshold

    @confidence_threshold.setter
    def confidence_threshold(self, value: float):
        self._confidence_threshold = value
        self.helmet_detector.settings["confidence_threshold"] = value
        self.plate_detector.settings["confidence_threshold"] = value
        self.traffic_light_detector.settings["confidence_threshold"] = value

    def configure_camera(self, camera_config: dict):
        if "road_direction" in camera_config:
            self.wrong_side_violation.configure(camera_config["road_direction"])
        if "stop_line" in camera_config and "traffic_light_roi" in camera_config:
            self.redlight_violation.configure(
                camera_config["stop_line"],
                camera_config["traffic_light_roi"],
            )

    def process_frame(self, frame: np.ndarray, camera_id: str = "CAM_01") -> list:
        self._frame_count += 1
        if self._frame_count % self.frame_skip != 0:
            return []

        violations = []

        helmet_detections = self.helmet_detector.detect_helmets(frame)
        light_detections = self.traffic_light_detector.detect_traffic_lights(frame)

        tracked_objects = self.tracker.update(helmet_detections, frame)

        helmet_violations = self.helmet_violation.process_frame(
            frame, tracked_objects, helmet_detections
        )
        for v in helmet_violations:
            violations.append(self._handle_violation(v, frame, camera_id))

        redlight_violations = self.redlight_violation.process_frame(
            frame, tracked_objects, light_detections
        )
        for v in redlight_violations:
            violations.append(self._handle_violation(v, frame, camera_id))

        wrong_side_violations = self.wrong_side_violation.process_frame(
            frame, tracked_objects, self.tracker
        )
        for v in wrong_side_violations:
            violations.append(self._handle_violation(v, frame, camera_id))

        return violations

    def _handle_violation(self, candidate, frame: np.ndarray, camera_id: str) -> ViolationResult:
        plate_number = None
        if candidate.best_frame is not None:
            plate_detections = self.plate_detector.detect_plates(candidate.best_frame)
            if plate_detections:
                best_plate = max(plate_detections, key=lambda d: d["confidence"])
                px1, py1, px2, py2 = best_plate["bbox"]
                plate_crop = candidate.best_frame[py1:py2, px1:px2]
                if plate_crop.size > 0:
                    ocr_result = self.ocr.read_plate(plate_crop)
                    if ocr_result:
                        plate_number = ocr_result["text"]

        rule = self.rules.get(candidate.violation_type, {})
        fine_amount = rule.get("fine_amount", 1000)

        evidence = self.evidence_gen.generate(
            frame=frame,
            violation_type=candidate.violation_type,
            track_id=candidate.track_id,
            bbox=candidate.bbox,
            plate_number=plate_number,
            confidence=candidate.best_confidence,
            camera_id=camera_id,
        )

        if evidence and candidate.best_frame is not None:
            plate_detections = self.plate_detector.detect_plates(candidate.best_frame)
            if plate_detections:
                best_plate = max(plate_detections, key=lambda d: d["confidence"])
                px1, py1, px2, py2 = best_plate["bbox"]
                plate_crop = candidate.best_frame[py1:py2, px1:px2]
                if plate_crop.size > 0:
                    self.evidence_gen.save_plate_crop(plate_crop, evidence["evidence_dir"])

        return ViolationResult(
            violation_id=evidence["violation_id"] if evidence else "unknown",
            violation_type=candidate.violation_type,
            track_id=candidate.track_id,
            plate_number=plate_number,
            confidence=candidate.best_confidence,
            fine_amount=fine_amount,
            evidence=evidence,
        )

    def reset(self):
        self.tracker.reset()
        self.helmet_violation.reset()
        self.redlight_violation.reset()
        self.wrong_side_violation.reset()
        self._frame_count = 0

    def process_image(self, image_path: str, camera_id: str = "CAM_01") -> list:
        frame = cv2.imread(image_path)
        if frame is None:
            raise ValueError(f"Could not read image: {image_path}")
        self.reset()
        self._frame_count = 0
        # Temporarily bypass frame_skip so single image always processes
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
