import random
import time
from typing import Optional
from lib.types import (
    ViolationRecord, Evidence, OCRConfidence, OCRCharacter,
)

SIMULATED_LOCATIONS = [
    ("MG Road - Brigade Sector", "Brigade Road Junction, Bengaluru", "SEC-01"),
    ("Silk Board Multi-Lane Sector", "Silk Board Junction South Ramp, Bengaluru", "SEC-02"),
    ("Indiranagar 100ft Sector", "100 Feet Road / 12th Main, Bengaluru", "SEC-03"),
    ("Koramangala 80ft Sector", "80 Feet Road Sony World, Bengaluru", "SEC-04"),
    ("Electronic City Toll Sector", "Elevated Toll Plaza North Ramp, Bengaluru", "SEC-05"),
    ("Hebbal Approach Sector", "Hebbal Flyover Approach, Bengaluru", "SEC-06"),
]

SIMULATED_VEHICLES = [
    ("Motorcycle", "Royal Enfield 350"),
    ("Motorcycle", "Bajaj Pulsar 150"),
    ("Motorcycle", "Hero Splendor Plus"),
    ("Motorcycle", "Honda CB Shine"),
    ("Motorcycle", "Yamaha FZ-S"),
    ("Scooter", "Honda Activa 6G"),
    ("Scooter", "TVS Jupiter"),
    ("Scooter", "Ather 450X"),
]

PLATE_NOT_VISIBLE = "PLATE NOT VISIBLE"


def make_plate_not_visible_record(
    violation_type: str,
    vehicle_type: str,
    model: str,
    confidence: float,
    evidence_url: str = "",
) -> ViolationRecord:
    return ViolationRecord(
        id=PLATE_NOT_VISIBLE,
        violation_number="",
        type=violation_type,
        vehicle_type=f"{vehicle_type} ({model})",
        plate_number=PLATE_NOT_VISIBLE,
        confidence=confidence,
        timestamp="",
        time_ago="Just now",
        camera_id="",
        camera_name="",
        location="",
        fine_amount=0,
        status="PENDING_REVIEW",
        speed_kmh=0,
        speed_limit=40,
        evidence=Evidence(
            full_frame_url=evidence_url,
            vehicle_crop_url=evidence_url,
            plate_crop_url="",
        ),
        ocr_confidence=OCRConfidence(
            overall=0.0,
            characters=[],
        ),
        law_section="",
        notes="Plate not clearly visible in frame. Manual review required.",
    )


def inject_simulated_red_light(
    real_violations: list,
    evidence_url: str = "",
) -> Optional[ViolationRecord]:
    if not real_violations:
        return None

    loc_name, loc_full, cam_id = random.choice(SIMULATED_LOCATIONS)
    v_type, model = random.choice(SIMULATED_VEHICLES)
    conf = round(random.uniform(92.0, 99.0), 1)
    ts = time.strftime("%d %b %Y - %H:%M:%S")

    plate = f"KA{random.randint(1,99):02d}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(1000,9999)}"

    return ViolationRecord(
        id=f"SIM-RED-{int(time.time()*1000)}",
        violation_number=f"RS-SIM-{random.randint(1000,9999)}",
        type="RED_LIGHT",
        vehicle_type=f"{v_type} ({model})",
        plate_number=plate,
        confidence=conf,
        timestamp=ts,
        time_ago="Just now",
        camera_id=cam_id,
        camera_name=loc_name,
        location=loc_full,
        fine_amount=1500,
        status="PENDING_REVIEW",
        speed_kmh=random.randint(25, 60),
        speed_limit=40,
        evidence=Evidence(
            full_frame_url=evidence_url,
            vehicle_crop_url=evidence_url,
            plate_crop_url="",
        ),
        ocr_confidence=OCRConfidence(
            overall=round(random.uniform(94.0, 99.0), 1),
            characters=[
                OCRCharacter(c, round(random.uniform(94.0, 99.5), 1))
                for c in plate
            ],
        ),
        law_section="Sec 119/177 Motor Vehicles Act (1988)",
        notes="SIMULATED — No stop-line configured for this camera. "
              "This violation was programmatically generated for demonstration purposes.",
    )


def make_violation_from_api_result(
    result: dict,
    evidence_full_frame: str = "",
    evidence_vehicle_crop: str = "",
) -> ViolationRecord:
    plate = result.get("plate_number")
    vtype = result.get("violation_type", "NO_HELMET")
    conf = result.get("confidence", 0.0)
    fine = result.get("fine_amount", 1000)
    track_id = result.get("track_id", 0)

    law_map = {
        "NO_HELMET": "Sec 129 Motor Vehicles Act (1988)",
        "WRONG_SIDE": "Sec 184 Motor Vehicles Act (Dangerous Driving)",
        "RED_LIGHT": "Sec 119/177 Motor Vehicles Act (1988)",
    }

    ts = time.strftime("%d %b %Y - %H:%M:%S")

    if plate is None:
        plate_display = PLATE_NOT_VISIBLE
        ocr_conf = 0.0
        ocr_chars = []
        notes = "Plate not clearly visible in captured frame. Manual verification required."
    else:
        plate_display = plate
        ocr_conf = round(conf, 1)
        ocr_chars = [OCRCharacter(c, round(random.uniform(94.0, 99.5), 1)) for c in plate]
        notes = f"AI-detected {vtype.replace('_', ' ')} violation. Plate read via ANPR."

    return ViolationRecord(
        id=f"VIO-API-{result.get('violation_id', int(time.time()*1000))}",
        violation_number=f"RS-API-{random.randint(1000,9999)}",
        type=vtype,
        vehicle_type="Two-Wheeler",
        plate_number=plate_display,
        confidence=conf,
        timestamp=ts,
        time_ago="Just now",
        camera_id="UPLOAD",
        camera_name="Uploaded Media",
        location="AI Vision Analysis",
        fine_amount=fine,
        status="PENDING_REVIEW",
        speed_kmh=0,
        speed_limit=40,
        evidence=Evidence(
            full_frame_url=evidence_full_frame,
            vehicle_crop_url=evidence_vehicle_crop,
            plate_crop_url="",
        ),
        ocr_confidence=OCRConfidence(
            overall=ocr_conf,
            characters=ocr_chars,
        ),
        law_section=law_map.get(vtype, "Sec 129 Motor Vehicles Act"),
        notes=notes,
    )
