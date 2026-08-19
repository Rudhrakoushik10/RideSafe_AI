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


def export_all_models():
    training_dir = Path("src/models/training")
    deployment_dir = Path("src/models/deployment")

    model_map = {
        "helmet": {
            "source": training_dir / "helmet" / "best.pt",
            "dest": deployment_dir / "helmet" / "helmet_detector.onnx",
        },
        "plate": {
            "source": training_dir / "numberplate" / "best.pt",
            "dest": deployment_dir / "plate" / "plate_detector.onnx",
        },
        "traffic_light": {
            "source": training_dir / "traffic_light" / "best.pt",
            "dest": deployment_dir / "traffic_light" / "traffic_light_detector.onnx",
        },
    }

    for name, paths in model_map.items():
        print(f"\n--- Exporting {name} model ---")
        source = str(paths["source"])
        dest = str(paths["dest"])
        export_model(source, dest)

    print("\nAll models exported.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        source = sys.argv[1]
        dest = sys.argv[2] if len(sys.argv) > 2 else source.replace(".pt", ".onnx")
        export_model(source, dest)
    else:
        export_all_models()
