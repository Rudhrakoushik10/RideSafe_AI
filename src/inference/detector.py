import cv2
import numpy as np
from pathlib import Path
from typing import Optional

import os
os.environ["ULTRALYTICS_NO_AUTOINSTALL"] = "1"

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

from ultralytics import YOLO

from src.config import get_model_path, get_device, get_inference_settings, load_config


class Detector:
    def __init__(self, model_type: str, config: dict = None):
        self.config = config or load_config()
        self.model_type = model_type
        self.settings = get_inference_settings(self.config)
        self.model = None
        self.device = "cpu"
        self._load_model()

    def _load_model(self):
        try:
            model_path = get_model_path(self.model_type, self.config)
            if model_path.endswith(".onnx") and ONNX_AVAILABLE:
                self.model = YOLO(model_path, task="detect")
            else:
                pt_path = model_path.replace(".onnx", ".pt")
                if Path(pt_path).exists():
                    self.model = YOLO(pt_path, task="detect")
                else:
                    self.model = YOLO(model_path, task="detect")
        except (FileNotFoundError, ValueError):
            self.model = None

    def detect(
        self,
        frame: np.ndarray,
        conf_threshold: Optional[float] = None,
        classes: Optional[list] = None,
    ) -> list:
        if self.model is None:
            return []
        conf = conf_threshold or self.settings["confidence_threshold"]
        imgsz = self.settings["image_size"]

        try:
            results = self.model.predict(
                source=frame,
                conf=conf,
                imgsz=imgsz,
                device="cpu",
                classes=classes,
                verbose=False,
            )
        except Exception as e:
            print(f"Detection error: {e}")
            return []

        detections = []
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    detections.append({
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "confidence": confidence,
                        "class_id": class_id,
                        "class_name": result.names.get(class_id, "unknown"),
                    })
        return detections


class MotorcycleDetector(Detector):
    MOTORCYCLE_CLASS_IDS = [3, 4]  # COCO: motorcycle=3, bicycle=4

    def __init__(self, config: dict = None):
        super().__init__(model_type="helmet", config=config)

    def detect_motorcycles(self, frame: np.ndarray) -> list:
        all_detections = self.detect(frame)
        return [d for d in all_detections if d["class_id"] in self.MOTORCYCLE_CLASS_IDS]


class HelmetDetector(Detector):
    TWO_WHEELER_CLASSES = {"with helmet", "without helmet", "helmet", "no helmet", "with_helmet", "without_helmet", "helmet_on"}

    def __init__(self, config: dict = None):
        super().__init__(model_type="helmet", config=config)

    def detect_helmets(self, frame: np.ndarray) -> list:
        all_detections = self.detect(frame)
        return self._filter_two_wheeler_detections(all_detections, frame)

    def _filter_two_wheeler_detections(self, detections: list, frame: np.ndarray) -> list:
        h, w = frame.shape[:2]
        frame_area = h * w
        filtered = []
        for det in detections:
            class_name = det.get("class_name", "").lower()
            if class_name == "licence":
                continue
            if class_name not in self.TWO_WHEELER_CLASSES:
                continue
            x1, y1, x2, y2 = det["bbox"]
            det_w = x2 - x1
            det_h = y2 - y1
            det_area = det_w * det_h
            if det_area < frame_area * 0.001:
                continue
            if det_area > frame_area * 0.5:
                continue
            if det_w > det_h * 1.5:
                continue
            filtered.append(det)
        return filtered


class PlateDetector(Detector):
    def __init__(self, config: dict = None):
        super().__init__(model_type="plate", config=config)

    def detect_plates(self, frame: np.ndarray) -> list:
        return self.detect(frame)


class TrafficLightDetector(Detector):
    def __init__(self, config: dict = None):
        super().__init__(model_type="traffic_light", config=config)

    def detect_traffic_lights(self, frame: np.ndarray) -> list:
        return self.detect(frame)
