import requests
import json
import os
import sys

API = "http://localhost:8000"
sys.path.insert(0, r"C:\Users\NAGANIKHIL SAI\Downloads\RideSafe_AI\ui")

# Test 1: API health
print("=== Test 1: API Health ===")
try:
    r = requests.get(f"{API}/api/dashboard", timeout=5)
    print(f"  Dashboard endpoint: {r.status_code} OK")
except Exception as e:
    print(f"  FAIL: {e}")
    exit(1)

# Test 2: Simulator
print("\n=== Test 2: Simulator ===")
from lib.simulator import inject_simulated_red_light, make_violation_from_api_result, PLATE_NOT_VISIBLE

fake_result = {
    "violation_id": "test_123",
    "violation_type": "NO_HELMET",
    "track_id": 1,
    "plate_number": None,
    "confidence": 95.3,
    "fine_amount": 1000,
}
rec = make_violation_from_api_result(fake_result)
print(f"  API result -> ViolationRecord: type={rec.type}, plate={rec.plate_number}")
assert rec.plate_number == PLATE_NOT_VISIBLE, f"Expected PLATE NOT VISIBLE, got {rec.plate_number}"
print(f"  PASS: plate correctly set to '{PLATE_NOT_VISIBLE}'")

# Test 3: Simulated red-light injection
print("\n=== Test 3: Red-Light Simulation ===")
sim_rl = inject_simulated_red_light([rec])
assert sim_rl is not None, "Expected simulated red-light"
assert sim_rl.type == "RED_LIGHT"
assert "SIMULATED" in sim_rl.notes
print(f"  PASS: Simulated RED_LIGHT injected")
print(f"    plate={sim_rl.plate_number}, conf={sim_rl.confidence}%, fine=Rs.{sim_rl.fine_amount}")
print(f"    notes={sim_rl.notes[:80]}...")

# Test 4: Mock data
print("\n=== Test 4: Mock Data ===")
from lib.mock_data import INITIAL_VIOLATIONS, PLATE_NOT_VISIBLE as MOCK_PNV
plate_vios = [v for v in INITIAL_VIOLATIONS if v.plate_number == MOCK_PNV]
sim_vios = [v for v in INITIAL_VIOLATIONS if v.type == "RED_LIGHT"]
print(f"  Total violations: {len(INITIAL_VIOLATIONS)}")
print(f"  Plate NOT VISIBLE: {len(plate_vios)}")
print(f"  RED_LIGHT (simulated): {len(sim_vios)}")
assert len(plate_vios) >= 2, "Expected at least 2 plate-not-visible violations"
assert len(sim_vios) >= 1, "Expected at least 1 simulated red-light"
print("  PASS")

# Test 5: Evidence endpoint
print("\n=== Test 5: Evidence Endpoint ===")
evidence_dir = r"C:\Users\NAGANIKHIL SAI\Downloads\RideSafe_AI\evidence"
if os.path.exists(evidence_dir):
    dates = os.listdir(evidence_dir)
    if dates:
        latest = sorted(dates)[-1]
        violations = os.listdir(os.path.join(evidence_dir, latest))
        if violations:
            v = violations[0]
            files = os.listdir(os.path.join(evidence_dir, latest, v))
            print(f"  Found evidence: {latest}/{v}/{files}")
            if "full_frame.jpg" in files:
                er = requests.get(f"{API}/api/evidence/{latest}/{v}/full_frame.jpg", timeout=5)
                print(f"  GET /api/evidence/.../full_frame.jpg: status={er.status_code}, size={len(er.content)} bytes")
                assert er.status_code == 200
                print("  PASS")
            else:
                print("  SKIP: no full_frame.jpg")
        else:
            print("  SKIP: no violations in evidence dir")
    else:
        print("  SKIP: no evidence dates")
else:
    print("  SKIP: no evidence dir yet")

# Test 6: Types
print("\n=== Test 6: UI Types ===")
from lib.types import ViolationRecord, Evidence, OCRConfidence, OCRCharacter, VehicleDetection
print("  All dataclasses importable")
print("  PASS")

print("\n========================================")
print("ALL TESTS PASSED")
print("========================================")
