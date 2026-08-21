import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ultralytics import YOLO


def train_helmet(data_yaml: str, epochs: int = 100, imgsz: int = 640, batch: int = 16, model_size: str = "s"):
    print(f"\n=== Training Helmet Detector (YOLOv8{model_size}) ===")
    model = YOLO(f"yolov8{model_size}.pt")

    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name=f"helmet_detect_{model_size}",
        project="training_runs/helmet_v2",
        exist_ok=True,
        patience=20,
        save=True,
        verbose=True,
        degrees=10,
        translate=0.2,
        scale=0.9,
        shear=5,
        perspective=0.001,
        mixup=0.2,
        copy_paste=0.3,
        fliplr=0.5,
        mosaic=1.0,
        erasing=0.4,
    )

    best_model = Path(f"training_runs/helmet_v2/helmet_detect_{model_size}/weights/best.pt")
    if best_model.exists():
        import shutil
        dest = Path("src/models/training/helmet/best.pt")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(best_model), str(dest))
        print(f"Best model saved to: {dest}")

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python train.py <data.yaml> [epochs] [batch] [model_size]")
        print("  Example: python train.py datasets/helmet/data_helmet_only.yaml 100 16 s")
        sys.exit(1)

    data_yaml = sys.argv[1]
    epochs = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    batch = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    model_size = sys.argv[4] if len(sys.argv) > 4 else "s"

    train_helmet(data_yaml, epochs, batch=batch, model_size=model_size)
