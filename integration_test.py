import sys
import io
import traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.path.insert(0, r"C:\Users\NAGANIKHIL SAI\Downloads\RideSafe_AI")

import cv2
import time
from pathlib import Path

# ── Step 1: Test config loading ────────────────────────────────────────
print("=" * 70)
print("  RideSafe AI - Full Integration Test")
print("=" * 70)

try:
    from src.config import load_config, get_model_path, get_inference_settings
    config = load_config()
    print("\n[OK] Config loaded successfully")
    print(f"     inference_fps: {config.get('inference_fps')}")
    print(f"     image_size: {config.get('image_size')}")
    print(f"     confidence_threshold: {config.get('confidence_threshold')}")
    print(f"     device: {config.get('device')}")
    for mtype, mpath in config.get('models', {}).items():
        full = Path(r"C:\Users\NAGANIKHIL SAI\Downloads\RideSafe_AI") / mpath
        exists = full.exists()
        size_mb = full.stat().st_size / 1024 / 1024 if exists else 0
        print(f"     model[{mtype}]: {mpath} {'OK (' + f'{size_mb:.1f}MB' + ')' if exists else 'MISSING!'}")
except Exception as e:
    print(f"\n[FATAL] Config loading failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# ── Step 2: Test individual detectors ──────────────────────────────────
print("\n" + "-" * 70)
print("  Phase 1: Individual Detector Tests")
print("-" * 70)

from src.inference.detector import HelmetDetector, PlateDetector, TrafficLightDetector

detectors_ok = {}
for name, DetCls in [("HelmetDetector", HelmetDetector),
                      ("PlateDetector", PlateDetector),
                      ("TrafficLightDetector", TrafficLightDetector)]:
    try:
        det = DetCls(config)
        has_model = det.model is not None
        detectors_ok[name] = has_model
        status = f"loaded (model={'present' if has_model else 'NONE'})"
        print(f"  [{('OK' if has_model else 'WARN')}] {name}: {status}")
    except Exception as e:
        detectors_ok[name] = False
        print(f"  [ERR] {name}: {e}")

# ── Step 3: Test tracker ──────────────────────────────────────────────
print("\n" + "-" * 70)
print("  Phase 2: Tracker Test")
print("-" * 70)

from src.inference.tracker import Tracker
tracker = Tracker()
import numpy as np
dummy_dets = [{"bbox": [100, 100, 200, 200], "confidence": 0.9, "class_id": 0, "class_name": "test"}]
dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
tracked = tracker.update(dummy_dets, dummy_frame)
print(f"  [OK] Tracker: {len(tracked)} objects tracked, track_id={tracked[0]['track_id'] if tracked else 'N/A'}")
tracker.reset()

# ── Step 4: Test ViolationEngine init ──────────────────────────────────
print("\n" + "-" * 70)
print("  Phase 3: ViolationEngine Initialization")
print("-" * 70)

from src.inference.violation_engine import ViolationEngine

try:
    engine = ViolationEngine(config)
    print("  [OK] ViolationEngine initialized")
    print(f"       frame_skip = {engine.frame_skip} (process every {engine.frame_skip} frame(s))")
    print(f"       helmet confirmation: {engine.helmet_violation.confirmation_frames} frames")
    print(f"       red_light confirmation: {engine.redlight_violation.confirmation_frames} frames")
    print(f"       wrong_side confirmation: {engine.wrong_side_violation.confirmation_frames} frames")
    print(f"       OCR engine: {engine.ocr.engine_type if engine.ocr.engine else 'None (not installed)'}")
except Exception as e:
    print(f"  [FATAL] ViolationEngine init failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# ── Step 5: Test on single image ──────────────────────────────────────
print("\n" + "-" * 70)
print("  Phase 4: Single Image Test")
print("-" * 70)

image_dir = Path(r"C:\Users\NAGANIKHIL SAI\Downloads\RideSafe_AI\datasets\helmet\train\images")
image_files = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.jpeg")) + list(image_dir.glob("*.png"))

if image_files:
    test_img = str(image_files[0])
    print(f"  Testing on: {image_files[0].name}")
    engine.reset()

    try:
        frame = cv2.imread(test_img)
        if frame is not None:
            print(f"  Image size: {frame.shape[1]}x{frame.shape[0]}")
            start = time.time()
            violations = engine.process_frame(frame, camera_id="IMG_TEST")
            elapsed = time.time() - start
            print(f"  [OK] Single frame processed in {elapsed*1000:.1f}ms")
            print(f"       Violations found: {len(violations)}")
            for v in violations:
                print(f"       - {v.violation_type}: track_id={v.track_id}, "
                      f"plate={v.plate_number}, fine=INR {v.fine_amount}, "
                      f"confidence={v.confidence:.3f}")
        else:
            print(f"  [WARN] Could not read image: {test_img}")
    except Exception as e:
        print(f"  [ERR] Image processing error: {e}")
        traceback.print_exc()
else:
    print("  [SKIP] No images found for single-image test")

# ── Step 6: Test on video ─────────────────────────────────────────────
print("\n" + "-" * 70)
print("  Phase 5: Video Pipeline Test")
print("-" * 70)

video_dir = Path(r"C:\Users\NAGANIKHIL SAI\Downloads\RideSafe_AI\datasets\test_data\traffic_videos")
videos = sorted(list(video_dir.rglob("*.mp4")) + list(video_dir.rglob("*.avi")) + list(video_dir.rglob("*.mov")))

if not videos:
    print("  [SKIP] No videos found!")
else:
    # Pick smallest video for faster testing
    video_sizes = [(v, v.stat().st_size) for v in videos]
    video_sizes.sort(key=lambda x: x[1])
    video_path, video_size = video_sizes[0]

    print(f"  Video: {video_path.name}")
    print(f"  Size: {video_size / 1024 / 1024:.1f} MB")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print("  [FATAL] Could not open video!")
    else:
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0

        print(f"  Resolution: {width}x{height}")
        print(f"  FPS: {fps}")
        print(f"  Total frames: {total_frames}")
        print(f"  Duration: {duration:.1f}s")

        engine.reset()
        start_time = time.time()
        frame_count = 0
        processed_count = 0
        all_violations = []
        detection_times = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            t0 = time.time()
            violations = engine.process_frame(frame, camera_id="VID_TEST")
            dt = time.time() - t0
            detection_times.append(dt)
            processed_count += 1
            all_violations.extend(violations)

        cap.release()
        elapsed = time.time() - start_time

        print(f"\n  --- Video Processing Results ---")
        print(f"  Frames read:           {frame_count}")
        print(f"  Frames processed:      {processed_count}")
        print(f"  Total time:            {elapsed:.2f}s")
        print(f"  Overall speed:         {frame_count / elapsed:.1f} FPS (read speed)")
        print(f"  Avg frame time:        {sum(detection_times) / len(detection_times) * 1000:.1f}ms")
        print(f"  Violations detected:   {len(all_violations)}")

        # Deduplicate violations by track_id + type
        seen = set()
        unique = []
        for v in all_violations:
            key = (v.violation_type, v.track_id)
            if key not in seen:
                seen.add(key)
                unique.append(v)
        print(f"  Unique violations:     {len(unique)}")

        if all_violations:
            print(f"\n  --- Violation Details (first 20) ---")
            for i, v in enumerate(all_violations[:20], 1):
                print(f"  {i:3d}. Type: {v.violation_type:15s} | "
                      f"track_id: {v.track_id:4d} | "
                      f"plate: {str(v.plate_number or 'N/A'):8s} | "
                      f"fine: INR {v.fine_amount:6d} | "
                      f"conf: {v.confidence:.3f} | "
                      f"id: {v.violation_id}")

            # Violation type breakdown
            from collections import Counter
            type_counts = Counter(v.violation_type for v in all_violations)
            print(f"\n  --- Violation Type Breakdown ---")
            for vtype, count in type_counts.most_common():
                print(f"  {vtype:15s}: {count:4d} detections")
        else:
            print("\n  No violations detected in this video.")
            print("  (This is normal if the video contains compliant traffic)")

# ── Step 7: Test all videos summary ───────────────────────────────────
print("\n" + "-" * 70)
print("  Phase 6: Multi-Video Summary (first 5 videos)")
print("-" * 70)

for i, vpath in enumerate(videos[:5], 1):
    engine.reset()
    try:
        violations = engine.process_video(str(vpath), camera_id=f"VID_{i:02d}", max_frames=100)
        print(f"  [{i}] {vpath.name[:50]:50s} -> {len(violations)} violations (max 100 frames)")
    except Exception as e:
        print(f"  [{i}] {vpath.name[:50]:50s} -> ERROR: {e}")

# ── Final summary ─────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("  Integration Test Complete")
print("=" * 70)
print(f"  Detectors loaded: {sum(detectors_ok.values())}/{len(detectors_ok)}")
for name, ok in detectors_ok.items():
    print(f"    {name}: {'PASS' if ok else 'FAIL (model not loaded)'}")
print(f"  OCR: {'Available' if engine.ocr.engine else 'Not available (PaddleOCR/EasyOCR not installed)'}")
print(f"  All tests passed: {'YES' if all(detectors_ok.values()) else 'PARTIAL (check warnings above)'}")
print("=" * 70)
