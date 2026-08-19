import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_config
from src.inference.violation_engine import ViolationEngine


def test_image(image_path: str):
    config = load_config()
    engine = ViolationEngine(config)

    print(f"Testing image: {image_path}")
    violations = engine.process_image(image_path)
    print(f"Found {len(violations)} violations")
    for v in violations:
        print(f"  - {v.violation_type}: track_id={v.track_id}, "
              f"plate={v.plate_number}, fine=₹{v.fine_amount}")
    return violations


def test_video(video_path: str, max_frames: int = 100):
    config = load_config()
    engine = ViolationEngine(config)

    print(f"Testing video: {video_path}")
    violations = engine.process_video(video_path, max_frames=max_frames)
    print(f"Found {len(violations)} violations")
    for v in violations:
        print(f"  - {v.violation_type}: track_id={v.track_id}, "
              f"plate={v.plate_number}, fine=₹{v.fine_amount}")
    return violations


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_inference.py <image_or_video_path>")
        sys.exit(1)

    path = sys.argv[1]
    ext = Path(path).suffix.lower()
    if ext in [".jpg", ".jpeg", ".png", ".bmp"]:
        test_image(path)
    elif ext in [".mp4", ".avi", ".mov", ".mkv"]:
        test_video(path)
    else:
        print(f"Unsupported file type: {ext}")
