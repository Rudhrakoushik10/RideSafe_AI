import cv2
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import numpy as np

from src.config import EVIDENCE_DIR, load_config


class EvidenceGenerator:
    def __init__(self, evidence_dir: str = None, config: dict = None):
        self.config = config or load_config()
        self.evidence_dir = Path(evidence_dir or EVIDENCE_DIR)
        self.save_evidence = self.config.get("save_evidence", True)

    def generate(
        self,
        frame: np.ndarray,
        violation_type: str,
        track_id: int,
        bbox: list,
        plate_number: Optional[str] = None,
        confidence: float = 0.0,
        camera_id: str = "CAM_01",
        timestamp: Optional[str] = None,
    ) -> Optional[dict]:
        violation_id = f"violation_{uuid.uuid4().hex[:8]}"

        if not self.save_evidence:
            return {
                "violation_id": violation_id,
                "metadata": {
                    "violation_id": violation_id,
                    "violation_type": violation_type,
                    "track_id": track_id,
                    "plate_number": plate_number,
                    "confidence": confidence,
                    "camera_id": camera_id,
                    "timestamp": timestamp or datetime.now().isoformat(),
                    "bbox": bbox,
                },
            }

        violation_id = f"violation_{uuid.uuid4().hex[:8]}"
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H-%M-%S")
        evidence_path = self.evidence_dir / date_str / f"{violation_id}"
        evidence_path.mkdir(parents=True, exist_ok=True)

        full_frame_path = evidence_path / "full_frame.jpg"
        cv2.imwrite(str(full_frame_path), frame)

        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        pad = 30
        crop = frame[max(0, y1-pad):min(h, y2+pad), max(0, x1-pad):min(w, x2+pad)]
        if crop.size > 0:
            vehicle_crop_path = evidence_path / "vehicle_crop.jpg"
            cv2.imwrite(str(vehicle_crop_path), crop)

        metadata = {
            "violation_id": violation_id,
            "violation_type": violation_type,
            "track_id": track_id,
            "plate_number": plate_number,
            "confidence": confidence,
            "camera_id": camera_id,
            "timestamp": timestamp or datetime.now().isoformat(),
            "bbox": bbox,
            "full_frame": str(full_frame_path),
            "vehicle_crop": str(vehicle_crop_path) if crop.size > 0 else None,
            "plate_crop": None,
        }

        metadata_path = evidence_path / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return {
            "violation_id": violation_id,
            "evidence_dir": str(evidence_path),
            "full_frame": str(full_frame_path),
            "vehicle_crop": str(vehicle_crop_path) if crop.size > 0 else None,
            "metadata": metadata,
        }

    def save_plate_crop(
        self, plate_crop: np.ndarray, evidence_dir: str
    ) -> Optional[str]:
        if plate_crop is None or plate_crop.size == 0:
            return None
        plate_path = Path(evidence_dir) / "plate_crop.jpg"
        cv2.imwrite(str(plate_path), plate_crop)
        return str(plate_path)
