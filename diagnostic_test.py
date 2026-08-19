"""Diagnostic script to find why 0 violations are detected."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.path.insert(0, r"C:\Users\NAGANIKHIL SAI\Downloads\RideSafe_AI")

import cv2
import numpy as np
from pathlib import Path
from src.config import load_config

config = load_config()

# ── Test 1: Raw model detections on a helmet dataset image ─────────────
print("=" * 70)
print("  DIAGNOSTIC 1: Raw Model Detections on Test Images")
print("=" * 70)

from src.inference.detector import HelmetDetector, PlateDetector, TrafficLightDetector

helmet_det = HelmetDetector(config)
plate_det = PlateDetector(config)
light_det = TrafficLightDetector(config)

# Test on helmet dataset images (known to have riders)
img_dir = Path(r"C:\Users\NAGANIKHIL SAI\Downloads\RideSafe_AI\datasets\helmet\test\images")
test_images = sorted(list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpeg")))[:5]

for img_path in test_images:
    frame = cv2.imread(str(img_path))
    if frame is None:
        continue
    print(f"\n  Image: {img_path.name} ({frame.shape[1]}x{frame.shape[0]})")

    # Run each detector at low threshold to see what the model produces
    helmet_dets = helmet_det.detect(frame, conf_threshold=0.1)
    plate_dets = plate_det.detect(frame, conf_threshold=0.1)
    light_dets = light_det.detect(frame, conf_threshold=0.1)

    print(f"    Helmet model:  {len(helmet_dets)} detections")
    for d in helmet_dets[:5]:
        print(f"      class={d['class_name']} (id={d['class_id']}) conf={d['confidence']:.3f} bbox={d['bbox']}")

    print(f"    Plate model:   {len(plate_dets)} detections")
    for d in plate_dets[:5]:
        print(f"      class={d['class_name']} (id={d['class_id']}) conf={d['confidence']:.3f} bbox={d['bbox']}")

    print(f"    Light model:   {len(light_dets)} detections")
    for d in light_dets[:5]:
        print(f"      class={d['class_name']} (id={d['class_id']}) conf={d['confidence']:.3f} bbox={d['bbox']}")

# ── Test 2: Check model class names ────────────────────────────────────
print("\n" + "=" * 70)
print("  DIAGNOSTIC 2: Model Class Names")
print("=" * 70)

for name, det in [("Helmet", helmet_det), ("Plate", plate_det), ("TrafficLight", light_det)]:
    if det.model is not None:
        names = det.model.names if hasattr(det.model, 'names') else {}
        print(f"  {name} model classes: {names}")
    else:
        print(f"  {name} model: NOT LOADED")

# ── Test 3: Tracker empty-list bug verification ────────────────────────
print("\n" + "=" * 70)
print("  DIAGNOSTIC 3: Tracker + ViolationEngine Bug Analysis")
print("=" * 70)

from src.inference.tracker import Tracker
from src.inference.violation_engine import ViolationEngine

engine = ViolationEngine(config)

# Use a test image from helmet dataset
if test_images:
    frame = cv2.imread(str(test_images[0]))

    # What does the helmet detector see?
    helmet_dets = helmet_det.detect(frame, conf_threshold=0.1)
    print(f"  Helmet detections on test image: {len(helmet_dets)}")
    for d in helmet_dets:
        print(f"    {d['class_name']} conf={d['confidence']:.3f}")

    # What does the tracker produce with empty input?
    tracker = Tracker()
    tracked_empty = tracker.update([], frame)
    print(f"\n  tracker.update([], frame) -> {len(tracked_empty)} objects")
    print(f"  ** This is the BUG: tracker receives empty detections from violation_engine.py line 73 **")

    # What would happen with real detections?
    tracked_with_dets = tracker.update(helmet_dets, frame)
    print(f"  tracker.update(helmet_dets, frame) -> {len(tracked_with_dets)} objects")
    for t in tracked_with_dets:
        print(f"    track_id={t['track_id']} class={t['class_name']} bbox={t['bbox']}")

    # The violation_engine always calls tracker.update([], frame)
    # meaning tracked_objects is ALWAYS empty -> no violations ever
    print(f"\n  ** violation_engine.py line 73 calls self.tracker.update([], frame) **")
    print(f"  ** This means tracked_objects is always empty [] **")
    print(f"  ** All violation detectors iterate over tracked_objects -> zero iterations -> zero violations **")

# ── Test 4: Simulate what WOULD happen with correct tracker flow ───────
print("\n" + "=" * 70)
print("  DIAGNOSTIC 4: Simulated Detection with Correct Flow")
print("=" * 70)

if test_images:
    engine.reset()
    frame = cv2.imread(str(test_images[0]))

    # Get detections from helmet detector
    helmet_dets = helmet_det.detect(frame, conf_threshold=0.1)
    print(f"  Detected {len(helmet_dets)} objects with helmet model")

    # Run tracker with actual detections
    engine.tracker.reset()
    tracked = engine.tracker.update(helmet_dets, frame)
    print(f"  Tracker produced {len(tracked)} tracked objects")

    # Now check helmet violations with proper tracked objects
    violations = engine.helmet_violation.process_frame(frame, tracked, helmet_dets)
    print(f"  Helmet violations (single frame): {len(violations)}")
    for v in violations:
        print(f"    {v.violation_type}: track_id={v.track_id} confirmed={v.confirmed}")

    # Multi-frame confirmation test
    print(f"\n  Running 10-frame confirmation test...")
    engine.helmet_violation.reset()
    engine.tracker.reset()
    all_v = []
    for i in range(10):
        tracked = engine.tracker.update(helmet_dets, frame)
        vs = engine.helmet_violation.process_frame(frame, tracked, helmet_dets)
        all_v.extend(vs)
        print(f"    Frame {i+1}: tracked={len(tracked)} violations={len(vs)} confirmed={[v.confirmed for v in vs]}")
    print(f"  Total violations after 10 frames: {len(all_v)}")
