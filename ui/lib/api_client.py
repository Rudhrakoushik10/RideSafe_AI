import requests
from typing import Optional


API_BASE = "http://localhost:8000"


def _api_url(path: str) -> str:
    return f"{API_BASE}{path}"


def health_check() -> bool:
    try:
        r = requests.get(_api_url("/api/dashboard"), timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def analyze_image(file_bytes: bytes, filename: str, camera_id: str = "CAM_01") -> dict:
    files = {"file": (filename, file_bytes, "image/jpeg")}
    r = requests.post(
        _api_url("/api/analyze/image"),
        files=files,
        params={"camera_id": camera_id},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()


def analyze_video(file_bytes: bytes, filename: str, camera_id: str = "CAM_01") -> dict:
    files = {"file": (filename, file_bytes, "video/mp4")}
    r = requests.post(
        _api_url("/api/analyze/video"),
        files=files,
        params={"camera_id": camera_id},
        timeout=300,
    )
    r.raise_for_status()
    return r.json()


def get_evidence_url(date_str: str, violation_id: str, filename: str) -> str:
    return _api_url(f"/api/evidence/{date_str}/{violation_id}/{filename}")


def get_dashboard() -> dict:
    r = requests.get(_api_url("/api/dashboard"), timeout=10)
    r.raise_for_status()
    return r.json()


def get_violations(skip: int = 0, limit: int = 50) -> dict:
    r = requests.get(
        _api_url("/api/violations"),
        params={"skip": skip, "limit": limit},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()
