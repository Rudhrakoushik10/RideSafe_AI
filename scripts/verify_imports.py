import sys
sys.path.insert(0, ".")

from src.config import load_config, load_camera_config, load_violation_rules
from src.inference.detector import HelmetDetector, PlateDetector, TrafficLightDetector
from src.inference.tracker import Tracker
from src.inference.helmet_violation import HelmetViolationDetector
from src.inference.redlight_violation import RedLightViolationDetector
from src.inference.wrong_side_violation import WrongSideViolationDetector
from src.inference.ocr import OCRReader
from src.inference.evidence import EvidenceGenerator
from src.inference.violation_engine import ViolationEngine
from database.models import init_db, seed_rules

print("All imports successful!")

config = load_config()
print(f"Config loaded: {len(config)} keys")
print(f"Cameras: {len(load_camera_config())}")
rules = load_violation_rules()
print(f"Rules: {list(rules['rules'].keys())}")

init_db()
print("Database initialized")
seed_rules()
print("Rules seeded")
print("System ready!")
