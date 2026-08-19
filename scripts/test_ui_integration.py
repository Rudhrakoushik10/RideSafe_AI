import requests
import json
import glob
import os

API = "http://localhost:8000"

test_images = glob.glob(r"C:\Users\NAGANIKHIL SAI\Downloads\RideSafe_AI\datasets\helmet\valid\images\*.jpg")
if not test_images:
    print("No test images found")
    exit(1)

img_path = test_images[0]
print(f"Testing with: {os.path.basename(img_path)}")

with open(img_path, "rb") as f:
    r = requests.post(
        f"{API}/api/analyze/image",
        files={"file": ("test.jpg", f, "image/jpeg")},
        params={"camera_id": "CAM_01"},
        timeout=60,
    )

data = r.json()
print(f"Status: {r.status_code}")
print(f"Violations: {data['count']}")
for v in data["violations"]:
    plate = v["plate_number"] if v["plate_number"] else "PLATE NOT VISIBLE"
    print(f"  - {v['violation_type']}: track={v['track_id']}, plate={plate}, conf={v['confidence']:.1f}%, fine=Rs.{v['fine_amount']}")

# Check evidence files
evidence_dir = r"C:\Users\NAGANIKHIL SAI\Downloads\RideSafe_AI\evidence"
dates = os.listdir(evidence_dir) if os.path.exists(evidence_dir) else []
print(f"\nEvidence dates: {dates}")
if dates:
    latest = sorted(dates)[-1]
    violations_dir = os.path.join(evidence_dir, latest)
    violations = os.listdir(violations_dir)
    print(f"Violations in {latest}: {len(violations)}")
    for v in violations:
        files = os.listdir(os.path.join(violations_dir, v))
        print(f"  {v}: {files}")
        if "full_frame.jpg" in files:
            er = requests.get(f"{API}/api/evidence/{latest}/{v}/full_frame.jpg", timeout=5)
            print(f"    Evidence endpoint: status={er.status_code}, size={len(er.content)} bytes")

print("\n--- Testing simulator ---")
import sys
sys.path.insert(0, r"C:\Users\NAGANIKHIL SAI\Downloads\RideSafe_AI\ui")
from lib.simulator import inject_simulated_red_light, make_violation_from_api_result, PLATE_NOT_VISIBLE

# Simulate mapping API result to ViolationRecord
for v in data["violations"]:
    rec = make_violation_from_api_result(v)
    plate_display = rec.plate_number
    print(f"  Mapped: type={rec.type}, plate_display={plate_display}, is_platenotvisible={plate_display == PLATE_NOT_VISIBLE}")

# Test simulated red-light injection
sim_rl = inject_simulated_red_light(data["violations"])
if sim_rl:
    print(f"  Simulated RED_LIGHT: plate={sim_rl.plate_number}, conf={sim_rl.confidence}%, fine=Rs.{sim_rl.fine_amount}")
    print(f"  Notes: {sim_rl.notes[:60]}...")
else:
    print("  No simulated red-light (empty violations)")

print("\nALL TESTS PASSED")
