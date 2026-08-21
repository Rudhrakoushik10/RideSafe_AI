import os
import yaml
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
MODELS_DIR = PROJECT_ROOT / "src" / "models"
DEPLOYMENT_MODELS_DIR = MODELS_DIR / "deployment"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"


def load_config(config_name: str = "inference.yaml") -> dict:
    config_path = CONFIG_DIR / config_name
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_device(config: dict = None) -> str:
    if config is None:
        config = load_config()
    return config.get("device", "auto")


def get_model_path(model_type: str, config: dict = None) -> str:
    if config is None:
        config = load_config()
    relative_path = config["models"].get(model_type)
    if relative_path is None:
        raise ValueError(f"Unknown model type: {model_type}")
    full_path = PROJECT_ROOT / relative_path
    if not full_path.exists():
        raise FileNotFoundError(f"Model not found: {full_path}")
    return str(full_path)


def get_inference_settings(config: dict = None) -> dict:
    if config is None:
        config = load_config()
    return {
        "inference_fps": int(config.get("inference_fps", 10)),
        "image_size": int(config.get("image_size", 640)),
        "confidence_threshold": float(config.get("confidence_threshold", 0.45)),
        "nms_threshold": config.get("nms_threshold", 0.45),
        "device": get_device(config),
    }


def load_camera_config() -> list:
    cameras_path = CONFIG_DIR / "cameras.json"
    with open(cameras_path, "r") as f:
        return json.load(f)


def load_violation_rules() -> dict:
    rules_path = CONFIG_DIR / "violation_rules.yaml"
    with open(rules_path, "r") as f:
        return yaml.safe_load(f)
