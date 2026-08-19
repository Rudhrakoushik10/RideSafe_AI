import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ultralytics import YOLO


def train_helmet(data_yaml: str, epochs: int = 100, imgsz: int = 640, batch: int = 16, model_size: str = "n"):
    print(f"\n=== Training Helmet Detector (YOLOv8{model_size}) ===")
    model = YOLO(f"yolov8{model_size}.pt")

    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name=f"helmet_detect_{model_size}",
        project="training_runs/helmet",
        exist_ok=True,
        patience=20,
        save=True,
        verbose=True,
    )

    best_model = Path(f"training_runs/helmet/helmet_detect_{model_size}/weights/best.pt")
    if best_model.exists():
        import shutil
        dest = Path("src/models/training/helmet/best.pt")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(best_model), str(dest))
        print(f"Best model saved to: {dest}")

    return results


def train_plate(data_yaml: str, epochs: int = 100, imgsz: int = 640, batch: int = 16, model_size: str = "n"):
    print(f"\n=== Training Plate Detector (YOLOv8{model_size}) ===")
    model = YOLO(f"yolov8{model_size}.pt")

    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name=f"plate_detect_{model_size}",
        project="training_runs/numberplate",
        exist_ok=True,
        patience=20,
        save=True,
        verbose=True,
    )

    best_model = Path(f"training_runs/numberplate/plate_detect_{model_size}/weights/best.pt")
    if best_model.exists():
        import shutil
        dest = Path("src/models/training/numberplate/best.pt")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(best_model), str(dest))
        print(f"Best model saved to: {dest}")

    return results


def train_traffic_light(data_yaml: str, epochs: int = 100, imgsz: int = 640, batch: int = 16, model_size: str = "n"):
    print(f"\n=== Training Traffic Light Detector (YOLOv8{model_size}) ===")
    model = YOLO(f"yolov8{model_size}.pt")

    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name=f"traffic_light_detect_{model_size}",
        project="training_runs/traffic_light",
        exist_ok=True,
        patience=20,
        save=True,
        verbose=True,
    )

    best_model = Path(f"training_runs/traffic_light/traffic_light_detect_{model_size}/weights/best.pt")
    if best_model.exists():
        import shutil
        dest = Path("src/models/training/traffic_light/best.pt")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(best_model), str(dest))
        print(f"Best model saved to: {dest}")

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python train.py helmet <data.yaml> [epochs] [batch] [model_size]")
        print("  python train.py plate <data.yaml> [epochs] [batch] [model_size]")
        print("  python train.py traffic_light <data.yaml> [epochs] [batch] [model_size]")
        sys.exit(1)

    task = sys.argv[1]
    data_yaml = sys.argv[2] if len(sys.argv) > 2 else "datasets/helmet/data.yaml"
    epochs = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    batch = int(sys.argv[4]) if len(sys.argv) > 4 else 16
    model_size = sys.argv[5] if len(sys.argv) > 5 else "n"

    if task == "helmet":
        train_helmet(data_yaml, epochs, batch=batch, model_size=model_size)
    elif task == "plate":
        train_plate(data_yaml, epochs, batch=batch, model_size=model_size)
    elif task == "traffic_light":
        train_traffic_light(data_yaml, epochs, batch=batch, model_size=model_size)
    else:
        print(f"Unknown task: {task}")
