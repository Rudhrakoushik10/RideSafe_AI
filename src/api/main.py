import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database.models import (
    get_db, init_db, seed_rules,
    Vehicle, Violation, Evidence, Camera, ViolationRule,
)
from src.config import load_config, load_camera_config
from src.inference.violation_engine import ViolationEngine

app = FastAPI(title="RideSafe AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine_instance: Optional[ViolationEngine] = None

EVIDENCE_DIR_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "evidence"))
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui", "static"))


@app.on_event("startup")
def startup():
    init_db()
    seed_rules()
    global engine_instance
    config = load_config()
    engine_instance = ViolationEngine(config)
    cameras = load_camera_config()
    if cameras:
        engine_instance.configure_camera(cameras[0])


def get_engine():
    return engine_instance


@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):
        with open(index_path, "r") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>RideSafe AI</h1><p>Static files not found.</p>")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.post("/api/analyze/image")
async def analyze_image(
    file: UploadFile = File(...),
    camera_id: str = Query(default="CAM_01"),
    confidence_threshold: float = Query(default=0.45, ge=0.05, le=0.95),
    mode: str = Query(default="auto"),
    db: Session = Depends(get_db),
    eng: ViolationEngine = Depends(get_engine),
):
    contents = await file.read()
    import cv2
    import numpy as np
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    eng.reset()
    saved_skip = eng.frame_skip
    eng.frame_skip = 1
    eng.confidence_threshold = confidence_threshold
    violations = eng.process_frame(frame, camera_id)
    eng.frame_skip = saved_skip

    if mode != "auto":
        mode_map = {"helmet": "NO_HELMET", "redlight": "RED_LIGHT", "wrongside": "WRONG_SIDE"}
        violations = [v for v in violations if v.violation_type == mode_map.get(mode)]

    results = []
    for v in violations:
        _save_violation_to_db(db, v)
        results.append({
            "violation_id": v.violation_id,
            "violation_type": v.violation_type,
            "track_id": v.track_id,
            "plate_number": v.plate_number,
            "confidence": v.confidence,
            "fine_amount": v.fine_amount,
            "bbox": v.evidence.get("metadata", {}).get("bbox") if v.evidence else None,
        })
    return {"violations": results, "count": len(results)}


@app.post("/api/analyze/video")
async def analyze_video(
    file: UploadFile = File(...),
    camera_id: str = Query(default="CAM_01"),
    confidence_threshold: float = Query(default=0.45, ge=0.05, le=0.95),
    mode: str = Query(default="auto"),
    db: Session = Depends(get_db),
    eng: ViolationEngine = Depends(get_engine),
):
    import tempfile
    import cv2

    suffix = os.path.splitext(file.filename)[1] if file.filename else ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        eng.confidence_threshold = confidence_threshold
        violations = eng.process_video(tmp_path, camera_id)
        if mode != "auto":
            mode_map = {"helmet": "NO_HELMET", "redlight": "RED_LIGHT", "wrongside": "WRONG_SIDE"}
            violations = [v for v in violations if v.violation_type == mode_map.get(mode)]
        results = []
        for v in violations:
            _save_violation_to_db(db, v)
            results.append({
                "violation_id": v.violation_id,
                "violation_type": v.violation_type,
                "track_id": v.track_id,
                "plate_number": v.plate_number,
                "confidence": v.confidence,
                "fine_amount": v.fine_amount,
                "bbox": v.evidence.get("metadata", {}).get("bbox") if v.evidence else None,
            })
        return {"violations": results, "count": len(results)}
    finally:
        os.unlink(tmp_path)


@app.get("/api/violations")
def get_violations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    violation_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Violation)
    if violation_type:
        query = query.filter(Violation.violation_type == violation_type)
    if status:
        query = query.filter(Violation.status == status)
    total = query.count()
    violations = query.order_by(desc(Violation.timestamp)).offset(skip).limit(limit).all()
    return {
        "total": total,
        "violations": [_violation_to_dict(v) for v in violations],
    }


@app.get("/api/violations/{violation_id}")
def get_violation_detail(violation_id: str, db: Session = Depends(get_db)):
    violation = db.query(Violation).filter(Violation.violation_id == violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")
    evidence = db.query(Evidence).filter(Evidence.violation_id == violation.id).all()
    return {
        "violation": _violation_to_dict(violation),
        "evidence": [_evidence_to_dict(e) for e in evidence],
    }


class StatusUpdate(BaseModel):
    status: str


@app.patch("/api/violations/{violation_id}")
def update_violation_status(violation_id: str, body: StatusUpdate, db: Session = Depends(get_db)):
    violation = db.query(Violation).filter(Violation.violation_id == violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")
    violation.status = body.status
    db.commit()
    return {"status": "updated", "violation_id": violation_id, "new_status": body.status}


@app.get("/api/analytics")
def get_analytics(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    total = db.query(Violation).filter(Violation.timestamp >= since).count()
    by_type = (
        db.query(Violation.violation_type, func.count(Violation.id))
        .filter(Violation.timestamp >= since)
        .group_by(Violation.violation_type)
        .all()
    )
    total_fines = (
        db.query(func.sum(Violation.fine_amount))
        .filter(Violation.timestamp >= since)
        .scalar() or 0
    )
    return {
        "total_violations": total,
        "total_simulated_fines": total_fines,
        "by_type": {t: c for t, c in by_type},
    }


@app.get("/api/cameras")
def get_cameras(db: Session = Depends(get_db)):
    cameras = db.query(Camera).all()
    return {"cameras": [_camera_to_dict(c) for c in cameras]}


@app.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(Violation).filter(Violation.timestamp >= today).count()
    today_fines = (
        db.query(func.sum(Violation.fine_amount))
        .filter(Violation.timestamp >= today)
        .scalar() or 0
    )
    total_count = db.query(Violation).count()
    recent = (
        db.query(Violation)
        .order_by(desc(Violation.timestamp))
        .limit(10)
        .all()
    )
    return {
        "today_violations": today_count,
        "today_fines": today_fines,
        "total_violations": total_count,
        "recent_violations": [_violation_to_dict(v) for v in recent],
    }


@app.get("/api/evidence/{date_str}/{violation_id}/{filename}")
def serve_evidence(date_str: str, violation_id: str, filename: str):
    file_path = os.path.join(EVIDENCE_DIR_PATH, date_str, violation_id, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Evidence file not found")
    return FileResponse(file_path)


def _save_violation_to_db(db: Session, v):
    existing = db.query(Violation).filter(Violation.violation_id == v.violation_id).first()
    if existing:
        return existing

    vehicle = None
    if v.plate_number:
        vehicle = db.query(Vehicle).filter(Vehicle.plate_number == v.plate_number).first()
        if not vehicle:
            vehicle = Vehicle(plate_number=v.plate_number)
            db.add(vehicle)
            db.flush()

    violation = Violation(
        violation_id=v.violation_id,
        vehicle_id=vehicle.id if vehicle else None,
        violation_type=v.violation_type,
        confidence=v.confidence,
        fine_amount=v.fine_amount,
        plate_number=v.plate_number,
        track_id=v.track_id,
        status="pending",
    )
    db.add(violation)
    db.flush()

    if v.evidence:
        evidence = Evidence(
            violation_id=violation.id,
            image_path=v.evidence.get("full_frame"),
            full_frame_path=v.evidence.get("full_frame"),
            vehicle_crop_path=v.evidence.get("vehicle_crop"),
            metadata_json=v.evidence.get("metadata"),
        )
        db.add(evidence)

    db.commit()
    return violation


def _violation_to_dict(v):
    return {
        "id": v.id,
        "violation_id": v.violation_id,
        "violation_type": v.violation_type,
        "timestamp": v.timestamp.isoformat() if v.timestamp else None,
        "confidence": v.confidence,
        "fine_amount": v.fine_amount,
        "status": v.status,
        "plate_number": v.plate_number,
        "track_id": v.track_id,
        "camera_id": v.camera_id,
    }


def _evidence_to_dict(e):
    return {
        "id": e.id,
        "image_path": e.image_path,
        "full_frame_path": e.full_frame_path,
        "vehicle_crop_path": e.vehicle_crop_path,
        "plate_crop_path": e.plate_crop_path,
        "video_timestamp": e.video_timestamp,
        "metadata_json": e.metadata_json,
    }


def _camera_to_dict(c):
    return {
        "id": c.id,
        "camera_id": c.camera_id,
        "name": c.name,
        "location": c.location,
        "configuration": c.configuration,
        "active": c.active,
    }
