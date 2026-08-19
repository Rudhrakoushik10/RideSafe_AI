import os
import sys
import yaml
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

DATASETS_DIR = Path("datasets")
TRAINING_DIR = Path("src/training")


def extract_zip(zip_path: str, dest_dir: str):
    import zipfile
    os.makedirs(dest_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(dest_dir)
    print(f"Extracted: {zip_path} -> {dest_dir}")


def prepare_helmet_dataset():
    print("\n=== Preparing Helmet Dataset ===")
    source = DATASETS_DIR / "Helmet and no helmet rider detection.yolov8 dataset.zip"
    dest = DATASETS_DIR / "helmet"

    if not source.exists():
        print(f"Source zip not found: {source}")
        return None

    if not dest.exists() or not any(dest.iterdir()):
        extract_zip(str(source), str(dest))

    data_yaml = find_data_yaml(dest)
    if data_yaml:
        print(f"Found data.yaml: {data_yaml}")
        return data_yaml

    print("No data.yaml found - manual setup may be needed")
    return None


def prepare_plate_dataset():
    print("\n=== Preparing License Plate Dataset ===")
    source = DATASETS_DIR / "Number plate dataset.zip"
    dest = DATASETS_DIR / "numberplate"

    if not source.exists():
        print(f"Source zip not found: {source}")
        return None

    if not dest.exists() or not any(dest.iterdir()):
        extract_zip(str(source), str(dest))

    data_yaml = find_data_yaml(dest)
    if data_yaml:
        print(f"Found data.yaml: {data_yaml}")
        return data_yaml

    print("No data.yaml found - manual setup may be needed")
    return None


def prepare_traffic_light_dataset():
    print("\n=== Preparing Traffic Light Dataset ===")
    source = DATASETS_DIR / "carla_traffic_light_dataset.zip"
    dest = DATASETS_DIR / "traffic_light"

    if not source.exists():
        print(f"Source zip not found: {source}")
        return None

    if not dest.exists() or not any(dest.iterdir()):
        extract_zip(str(source), str(dest))

    data_yaml = find_data_yaml(dest)
    if data_yaml:
        print(f"Found data.yaml: {data_yaml}")
        return data_yaml

    print("No data.yaml found - manual setup may be needed")
    return None


def prepare_test_videos():
    print("\n=== Preparing Test Videos ===")
    source = DATASETS_DIR / "traffic videos dataset.zip"
    dest = DATASETS_DIR / "test_data" / "traffic_videos"

    if not source.exists():
        print(f"Source zip not found: {source}")
        return None

    if not dest.exists() or not any(dest.iterdir()):
        extract_zip(str(source), str(dest))

    videos = list(dest.rglob("*.mp4")) + list(dest.rglob("*.avi")) + list(dest.rglob("*.mov"))
    print(f"Found {len(videos)} test videos")
    return str(dest)


def find_data_yaml(dataset_dir: Path) -> str:
    for pattern in ["**/data.yaml", "**/data.yml", "**/dataset.yaml"]:
        found = list(dataset_dir.glob(pattern))
        if found:
            return str(found[0])
    return None


def inspect_dataset(data_yaml_path: str):
    if not data_yaml_path or not os.path.exists(data_yaml_path):
        print("No data.yaml to inspect")
        return

    with open(data_yaml_path, "r") as f:
        data = yaml.safe_load(f)

    print(f"\nDataset: {data_yaml_path}")
    print(f"  Classes: {data.get('names', [])}")
    print(f"  Train: {data.get('train', 'N/A')}")
    print(f"  Val: {data.get('val', 'N/A')}")

    train_path = data.get("train", "")
    if train_path:
        train_dir = Path(data_yaml_path).parent / train_path
        if train_dir.exists():
            images = list(train_dir.glob("**/*.jpg")) + list(train_dir.glob("**/*.png"))
            print(f"  Training images: {len(images)}")

    val_path = data.get("val", "")
    if val_path:
        val_dir = Path(data_yaml_path).parent / val_path
        if val_dir.exists():
            images = list(val_dir.glob("**/*.jpg")) + list(val_dir.glob("**/*.png"))
            print(f"  Validation images: {len(images)}")


def validate_dataset(data_yaml_path: str):
    if not data_yaml_path:
        return False

    with open(data_yaml_path, "r") as f:
        data = yaml.safe_load(f)

    issues = []

    train_path = data.get("train")
    val_path = data.get("val")

    if not train_path:
        issues.append("No 'train' path defined")
    if not val_path:
        issues.append("No 'val' path defined")
    if not data.get("names"):
        issues.append("No class names defined")

    if issues:
        print(f"\nDataset issues for {data_yaml_path}:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print(f"\nDataset validation passed: {data_yaml_path}")
    return True


def prepare_all():
    print("Preparing all datasets...")
    results = {
        "helmet": prepare_helmet_dataset(),
        "numberplate": prepare_plate_dataset(),
        "traffic_light": prepare_traffic_light_dataset(),
        "test_videos": prepare_test_videos(),
    }

    print("\n=== Dataset Summary ===")
    for name, path in results.items():
        status = "OK" if path else "MISSING"
        print(f"  {name}: {status}")

    for name, path in results.items():
        if name != "test_videos" and path:
            inspect_dataset(path)
            validate_dataset(path)

    return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        dataset = sys.argv[1]
        if dataset == "helmet":
            path = prepare_helmet_dataset()
            inspect_dataset(path)
        elif dataset == "plate":
            path = prepare_plate_dataset()
            inspect_dataset(path)
        elif dataset == "traffic_light":
            path = prepare_traffic_light_dataset()
            inspect_dataset(path)
        elif dataset == "test_videos":
            prepare_test_videos()
        else:
            print(f"Unknown dataset: {dataset}")
    else:
        prepare_all()
