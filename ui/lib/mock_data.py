from lib.types import (
    ViolationRecord, Evidence, OCRConfidence, OCRCharacter, VehicleDetection
)

PLATE_NOT_VISIBLE = "PLATE NOT VISIBLE"

INITIAL_VIOLATIONS = [
    ViolationRecord(
        id="VIO-2026-8941",
        violation_number="RS-KA04-8941",
        type="NO_HELMET",
        vehicle_type="Motorcycle (Royal Enfield 350)",
        plate_number=PLATE_NOT_VISIBLE,
        confidence=96.4,
        timestamp="18 Aug 2026 - 18:42:16",
        time_ago="Just now",
        camera_id="SEC-01",
        camera_name="MG Road - Brigade Sector",
        location="Brigade Road Junction, Bengaluru",
        fine_amount=1000,
        status="PENDING_REVIEW",
        speed_kmh=47,
        speed_limit=40,
        evidence=Evidence(
            full_frame_url="",
            vehicle_crop_url="",
            plate_crop_url="",
        ),
        ocr_confidence=OCRConfidence(overall=0.0, characters=[]),
        law_section="Sec 129 Motor Vehicles Act (1988)",
        notes="Plate not clearly visible in captured frame. Manual verification required.",
    ),
    ViolationRecord(
        id="VIO-2026-8940",
        violation_number="RS-KA01-8940",
        type="RED_LIGHT",
        vehicle_type="Motorcycle (Yamaha FZ)",
        plate_number="KA01AB1234",
        confidence=97.8,
        timestamp="18 Aug 2026 - 18:39:04",
        time_ago="3m ago",
        camera_id="SEC-02",
        camera_name="Silk Board Multi-Lane Sector",
        location="Silk Board Junction South Ramp, Bengaluru",
        fine_amount=1500,
        status="CHALLAN_ISSUED",
        speed_kmh=54,
        speed_limit=40,
        evidence=Evidence(
            full_frame_url="",
            vehicle_crop_url="",
            plate_crop_url="",
        ),
        ocr_confidence=OCRConfidence(
            overall=98.4,
            characters=[
                OCRCharacter("K", 99.4), OCRCharacter("A", 99.1),
                OCRCharacter("0", 98.8), OCRCharacter("1", 99.0),
                OCRCharacter("A", 97.8), OCRCharacter("B", 98.1),
                OCRCharacter("1", 98.7), OCRCharacter("2", 98.3),
                OCRCharacter("3", 97.9), OCRCharacter("4", 98.2),
            ],
        ),
        law_section="Sec 119/177 Motor Vehicles Act (1988)",
        notes="SIMULATED — No stop-line configured for this camera. "
              "This violation was programmatically generated for demonstration purposes.",
    ),
    ViolationRecord(
        id="VIO-2026-8939",
        violation_number="RS-KA03-8939",
        type="WRONG_SIDE",
        vehicle_type="Scooter (TVS Jupiter)",
        plate_number=PLATE_NOT_VISIBLE,
        confidence=94.9,
        timestamp="18 Aug 2026 - 18:31:45",
        time_ago="11m ago",
        camera_id="SEC-03",
        camera_name="Indiranagar 100ft Sector",
        location="100 Feet Road / 12th Main, Bengaluru",
        fine_amount=2000,
        status="VERIFIED",
        speed_kmh=29,
        speed_limit=40,
        evidence=Evidence(
            full_frame_url="",
            vehicle_crop_url="",
            plate_crop_url="",
        ),
        ocr_confidence=OCRConfidence(overall=0.0, characters=[]),
        law_section="Sec 184 Motor Vehicles Act (Dangerous Driving)",
        notes="Plate not clearly visible in captured frame. Manual verification required.",
    ),
    ViolationRecord(
        id="VIO-2026-8938",
        violation_number="RS-KA53-8938",
        type="NO_HELMET",
        vehicle_type="Motorcycle (Bajaj Pulsar)",
        plate_number=PLATE_NOT_VISIBLE,
        confidence=93.6,
        timestamp="18 Aug 2026 - 18:22:11",
        time_ago="20m ago",
        camera_id="SEC-04",
        camera_name="Koramangala 80ft Sector",
        location="80 Feet Road Sony World, Bengaluru",
        fine_amount=1000,
        status="CHALLAN_ISSUED",
        speed_kmh=38,
        speed_limit=40,
        evidence=Evidence(
            full_frame_url="",
            vehicle_crop_url="",
            plate_crop_url="",
        ),
        ocr_confidence=OCRConfidence(overall=0.0, characters=[]),
        law_section="Sec 129 Motor Vehicles Act (1988)",
        notes="Plate not clearly visible in captured frame. Manual verification required.",
    ),
    ViolationRecord(
        id="VIO-2026-8937",
        violation_number="RS-KA02-8937",
        type="RED_LIGHT",
        vehicle_type="Scooter (Ather 450X)",
        plate_number="KA02GH3456",
        confidence=98.2,
        timestamp="18 Aug 2026 - 18:14:02",
        time_ago="28m ago",
        camera_id="SEC-05",
        camera_name="Electronic City Toll Sector",
        location="Elevated Toll Plaza North Ramp, Bengaluru",
        fine_amount=1500,
        status="PAID",
        speed_kmh=42,
        speed_limit=40,
        evidence=Evidence(
            full_frame_url="",
            vehicle_crop_url="",
            plate_crop_url="",
        ),
        ocr_confidence=OCRConfidence(
            overall=98.9,
            characters=[
                OCRCharacter("K", 99.2), OCRCharacter("A", 99.0),
                OCRCharacter("0", 98.9), OCRCharacter("2", 99.1),
                OCRCharacter("G", 98.2), OCRCharacter("H", 98.7),
                OCRCharacter("3", 99.3), OCRCharacter("4", 98.9),
                OCRCharacter("5", 98.5), OCRCharacter("6", 99.0),
            ],
        ),
        law_section="Sec 119/177 Motor Vehicles Act (1988)",
        notes="SIMULATED — No stop-line configured for this camera. "
              "This violation was programmatically generated for demonstration purposes. "
              "Fine settlement received online.",
    ),
]

DEFAULT_DETECTIONS = [
    VehicleDetection(
        id="det-custom-1",
        tracking_id="TRK-#401",
        vehicle_type="Motorcycle",
        model="Hero Splendor Plus",
        plate_number=PLATE_NOT_VISIBLE,
        confidence=96.5,
        helmet_status="NOT_DETECTED",
        speed_kmh=45,
        direction="NORTH_BOUND",
        is_violating=True,
        violation_type="NO_HELMET",
        box={"x": 28, "y": 32, "width": 36, "height": 50},
        head_box={"x": 40, "y": 34, "width": 11, "height": 13},
        plate_box=None,
    ),
    VehicleDetection(
        id="det-custom-2",
        tracking_id="TRK-#402",
        vehicle_type="Scooter",
        model="Honda Activa",
        plate_number=PLATE_NOT_VISIBLE,
        confidence=94.8,
        helmet_status="DETECTED",
        speed_kmh=32,
        direction="NORTH_BOUND",
        is_violating=False,
        box={"x": 68, "y": 42, "width": 25, "height": 40},
        head_box={"x": 74, "y": 44, "width": 9, "height": 11},
        plate_box=None,
    ),
]

HOURLY_DATA = [
    {"hour": "06:00", "total": 12, "no_helmet": 6, "red_light": 4, "wrong_side": 2},
    {"hour": "08:00", "total": 48, "no_helmet": 26, "red_light": 14, "wrong_side": 8},
    {"hour": "10:00", "total": 84, "no_helmet": 42, "red_light": 28, "wrong_side": 14},
    {"hour": "12:00", "total": 52, "no_helmet": 28, "red_light": 16, "wrong_side": 8},
    {"hour": "14:00", "total": 44, "no_helmet": 22, "red_light": 14, "wrong_side": 8},
    {"hour": "16:00", "total": 68, "no_helmet": 36, "red_light": 20, "wrong_side": 12},
    {"hour": "18:00", "total": 112, "no_helmet": 58, "red_light": 34, "wrong_side": 20},
    {"hour": "20:00", "total": 96, "no_helmet": 52, "red_light": 28, "wrong_side": 16},
    {"hour": "22:00", "total": 38, "no_helmet": 20, "red_light": 12, "wrong_side": 6},
]

HEATMAP_HOURS = ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00"]
HEATMAP_DATA = {
    "MG Road Sector": [8, 14, 9, 7, 11, 24, 18],
    "Silk Board Sector": [12, 19, 11, 9, 15, 32, 26],
    "Indiranagar 100ft Sector": [6, 11, 8, 5, 9, 18, 14],
    "Koramangala 80ft Sector": [7, 13, 7, 6, 12, 22, 16],
    "Electronic City Sector": [9, 16, 10, 8, 14, 28, 22],
    "Hebbal Approach Sector": [5, 9, 6, 4, 8, 14, 10],
}

VIOLATION_BADGES = {
    "NO_HELMET": {"label": "NO HELMET", "color": "red", "icon": "hard_hat"},
    "NO_HELMET_PILLION": {"label": "NO HELMET", "color": "red", "icon": "hard_hat"},
    "RED_LIGHT": {"label": "RED LIGHT", "color": "red", "icon": "alert_octagon"},
    "WRONG_SIDE": {"label": "WRONG SIDE", "color": "orange", "icon": "compass"},
}

FINE_AMOUNTS = {
    "NO_HELMET": 1000,
    "NO_HELMET_PILLION": 1000,
    "RED_LIGHT": 1500,
    "WRONG_SIDE": 2000,
}

LAW_SECTIONS = {
    "NO_HELMET": "Sec 129 Motor Vehicles Act (1988)",
    "RED_LIGHT": "Sec 119/177 Motor Vehicles Act (1988)",
    "WRONG_SIDE": "Sec 184 Motor Vehicles Act (Dangerous Driving)",
}
