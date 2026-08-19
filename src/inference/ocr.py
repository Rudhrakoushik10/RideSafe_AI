import cv2
import numpy as np
from typing import Optional


class OCRReader:
    def __init__(self, confidence_threshold: float = 0.6):
        self.confidence_threshold = confidence_threshold
        self.engine = None
        self._init_engine()

    def _init_engine(self):
        try:
            from paddleocr import PaddleOCR
            self.engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            self.engine_type = "paddle"
        except ImportError:
            try:
                import easyocr
                self.engine = easyocr.Reader(["en"])
                self.engine_type = "easyocr"
            except ImportError:
                self.engine = None
                self.engine_type = None

    def read_plate(self, plate_crop: np.ndarray) -> Optional[dict]:
        if self.engine is None or plate_crop is None or plate_crop.size == 0:
            return None

        if len(plate_crop.shape) == 3:
            gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_crop.copy()

        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        if self.engine_type == "paddle":
            return self._read_paddle(binary)
        elif self.engine_type == "easyocr":
            return self._read_easyocr(binary)
        return None

    def _read_paddle(self, image: np.ndarray) -> Optional[dict]:
        try:
            results = self.engine.ocr(image, cls=True)
            if results is None or len(results) == 0:
                return None
            texts = []
            for line in results[0]:
                if line and len(line) >= 2:
                    text = line[1][0]
                    conf = line[1][1]
                    if conf >= self.confidence_threshold:
                        texts.append(text)
            if texts:
                plate_text = "".join(texts).upper().replace(" ", "")
                return {"text": plate_text, "confidence": conf, "raw_texts": texts}
        except Exception as e:
            print(f"PaddleOCR error: {e}")
        return None

    def _read_easyocr(self, image: np.ndarray) -> Optional[dict]:
        try:
            results = self.engine.readtext(image)
            texts = []
            for (bbox, text, conf) in results:
                if conf >= self.confidence_threshold:
                    texts.append(text)
            if texts:
                plate_text = "".join(texts).upper().replace(" ", "")
                return {"text": plate_text, "confidence": conf, "raw_texts": texts}
        except Exception as e:
            print(f"EasyOCR error: {e}")
        return None
