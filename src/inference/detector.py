import cv2
import numpy as np
from pathlib import Path
from typing import Optional

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
        self.device = get_device(self.config)
        self._load_model()

    def _load_model(self):
        try:
            model_path = get_model_path(self.model_type, self.config)
            if model_path.endswith(".onnx") and ONNX_AVAILABLE:
                self.model = YOLO(model_path)
            else:
                pt_path = model_path.replace(".onnx", ".pt")
                if Path(pt_path).exists():
                    self.model = YOLO(pt_path)
                else:
                    self.model = YOLO(model_path)
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
        device = self.device

        try:
            results = self.model.predict(
                source=frame,
                conf=conf,
                imgsz=imgsz,
                device=device if device != "auto" else None,
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
    def __init__(self, config: dict = None):
        super().__init__(model_type="helmet", config=config)

    def detect_helmets(self, frame: np.ndarray) -> list:
        return self.detect(frame)


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
