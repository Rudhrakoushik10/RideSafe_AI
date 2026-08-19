from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ViolationType(str, Enum):
    NO_HELMET = "NO_HELMET"
    RED_LIGHT = "RED_LIGHT"
    WRONG_SIDE = "WRONG_SIDE"
    NO_HELMET_PILLION = "NO_HELMET_PILLION"


class ViolationStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    CHALLAN_ISSUED = "CHALLAN_ISSUED"
    VERIFIED = "VERIFIED"
    DISMISSED = "DISMISSED"
    APPROVED = "APPROVED"
    PAID = "PAID"


class PageType(str, Enum):
    UPLOAD = "upload"
    VIOLATIONS = "violations"
    ANALYTICS = "analytics"
    VIOLATION_DETAIL = "violation_detail"
    ECHALLAN = "echallan"


@dataclass
class Evidence:
    full_frame_url: str
    vehicle_crop_url: str
    plate_crop_url: str
    helmet_crop_url: Optional[str] = None


@dataclass
class OCRCharacter:
    char: str
    confidence: float


@dataclass
class OCRConfidence:
    overall: float
    characters: list[OCRCharacter] = field(default_factory=list)


@dataclass
class VehicleDetection:
    id: str
    tracking_id: str
    vehicle_type: str
    model: str
    plate_number: str
    confidence: float
    helmet_status: str
    speed_kmh: float
    direction: str
    is_violating: bool
    violation_type: Optional[str] = None
    box: dict = field(default_factory=dict)
    head_box: Optional[dict] = None
    plate_box: Optional[dict] = None


@dataclass
class ViolationRecord:
    id: str
    violation_number: str
    type: str
    vehicle_type: str
    plate_number: str
    confidence: float
    timestamp: str
    time_ago: str
    camera_id: str
    camera_name: str
    location: str
    fine_amount: int
    status: str
    speed_kmh: float
    speed_limit: float
    evidence: Evidence
    ocr_confidence: OCRConfidence
    law_section: str
    notes: str = ""


@dataclass
class UploadedMediaAnalysis:
    id: str
    file_name: str
    file_type: str
    media_url: str
    status: str
    progress: float
    current_step: str
    detections: list[VehicleDetection] = field(default_factory=list)
    violations_detected: int = 0
    motorcycles_detected: int = 0
    helmet_compliance_rate: float = 0.0
    processing_time_ms: float = 0.0
    timestamp: str = ""
