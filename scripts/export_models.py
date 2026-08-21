import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ultralytics import YOLO


def export_model(source_path: str, output_path: str, imgsz: int = 640):
    if not os.path.exists(source_path):
        print(f"Source model not found: {source_path}")
        return False

    print(f"Loading model: {source_path}")
    model = YOLO(source_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Exporting to ONNX: {output_path}")
    model.export(format="onnx", imgsz=imgsz, opset=13)

    exported_name = Path(source_path).stem + ".onnx"
    exported_path = Path(source_path).parent / exported_name
    if exported_path.exists():
        os.rename(str(exported_path), output_path)
        print(f"Exported: {output_path}")
        return True

    print(f"Model exported to: {output_path}")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        source = sys.argv[1]
        dest = sys.argv[2] if len(sys.argv) > 2 else source.replace(".pt", ".onnx")
    else:
        source = "src/models/training/helmet/best.pt"
        dest = "src/models/deployment/helmet/helmet_detector.onnx"

    export_model(source, dest)
