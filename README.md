# RideSafe AI

Real-time traffic violation detection system for two-wheelers using YOLOv8 computer vision models. Detects helmet violations, red-light crossings, and wrong-side riding with automated evidence capture and e-Challan integration.

## Features

- **Helmet Detection** -- Classifies riders as with/without helmet using YOLOv8
- **Red-Light Violation** -- Detects vehicles crossing stop lines during red signals
- **Wrong-Side Detection** -- Identifies two-wheelers riding against road direction
- **License Plate Recognition** -- ONNX-powered ANPR with PaddleOCR fallback
- **Object Tracking** -- IoU-based re-identification across video frames
- **Evidence Generation** -- Automatic full-frame, vehicle crop, and plate crop capture
- **Web Interface** -- Dark-theme SPA with real-time analysis, Chart.js visualizations, CSV export
- **REST API** -- FastAPI endpoints for image/video analysis, violation management, analytics

## Project Structure

```
RideSafe_AI/
├── config/
│   ├── inference.yaml          # Model paths, thresholds, inference settings
│   ├── violation_rules.yaml    # Fine amounts per violation type
│   └── cameras.json            # Camera configurations (ROI, stop lines)
├── database/
│   └── models.py               # SQLAlchemy ORM (Vehicle, Violation, Evidence, Camera)
├── scripts/
│   ├── train.py                # YOLOv8 training CLI
│   ├── export_models.py        # .pt to ONNX conversion
│   ├── prepare_datasets.py     # Dataset extraction and validation
│   ├── convert_datasets.py     # VOC/CSV to YOLO format conversion
│   └── test_inference.py       # CLI inference test
├── src/
│   ├── config.py               # Config loader and path resolution
│   ├── api/
│   │   └── main.py             # FastAPI application
│   ├── inference/
│   │   ├── detector.py         # YOLO model wrappers (Helmet, Plate, TrafficLight)
│   │   ├── tracker.py          # IoU-based object tracker
│   │   ├── helmet_violation.py # Helmet violation logic
│   │   ├── redlight_violation.py # Red-light violation logic
│   │   ├── wrong_side_violation.py # Wrong-side violation logic
│   │   ├── ocr.py              # PaddleOCR license plate reader
│   │   ├── evidence.py         # Evidence crop generation
│   │   └── violation_engine.py # Master inference pipeline
│   └── models/
│       └── deployment/         # ONNX models (~11.7MB each)
│           ├── helmet/helmet_detector.onnx
│           ├── plate/plate_detector.onnx
│           └── traffic_light/traffic_light_detector.onnx
├── ui/
│   └── static/
│       ├── index.html          # Single-page application
│       ├── css/styles.css      # Dark theme styles
│       └── js/app.js           # Frontend logic, Chart.js, canvas overlays
├── requirements-inference.txt  # Production dependencies
├── requirements-training.txt   # Training dependencies
├── start.bat                   # Single-server launcher (port 8000)
├── .env.example                # Environment variable template
└── .gitignore
```

## Quick Start

### Prerequisites

- Python 3.9+
- CUDA 12.6+ (for GPU training) or CPU-only (for inference)
- 4GB+ RAM

### Installation

```bash
# Clone the repository
git clone https://github.com/Rudhrakoushik10/RideSafe_AI.git
cd RideSafe_AI

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate    # Linux/Mac

# Install dependencies
pip install -r requirements-inference.txt

# Copy environment config
copy .env.example .env          # Windows
# cp .env.example .env         # Linux/Mac
```

### Running the Server

```bash
# Windows
start.bat

# Or manually
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000` in your browser.

### CLI Inference

```bash
python scripts/test_inference.py path/to/image.jpg
python scripts/test_inference.py path/to/video.mp4
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze/image` | Analyze image for violations |
| `POST` | `/api/analyze/video` | Analyze video for violations |
| `GET` | `/api/violations` | List violations (filterable by type/status) |
| `GET` | `/api/violations/{id}` | Get violation detail with evidence |
| `PATCH` | `/api/violations/{id}` | Update violation status (approved/dismissed) |
| `GET` | `/api/analytics` | Aggregated violation statistics |
| `GET` | `/api/cameras` | List configured cameras |
| `GET` | `/api/dashboard` | Dashboard summary (today's counts, fines) |
| `GET` | `/api/evidence/{date}/{id}/{file}` | Serve evidence files |

### Analyze Image

```bash
curl -X POST "http://localhost:8000/api/analyze/image?confidence_threshold=0.45&mode=auto" \
  -F "file=@photo.jpg"
```

**Query Parameters:**
- `camera_id` -- Camera identifier (default: `CAM_01`)
- `confidence_threshold` -- Detection threshold 0.05-0.95 (default: `0.45`)
- `mode` -- `auto`, `helmet`, `redlight`, or `wrongside`

**Response:**
```json
{
  "violations": [
    {
      "violation_id": "violation_abc123",
      "violation_type": "NO_HELMET",
      "track_id": 1,
      "plate_number": "MH12AB1234",
      "confidence": 87,
      "fine_amount": 1000,
      "bbox": [120, 80, 340, 420]
    }
  ],
  "count": 1
}
```

## Training

### Datasets

Place dataset ZIP files in `datasets/`:

```
datasets/
├── helmet_data.zip          # With Helmet / Without Helmet / Licence classes
├── numberplate_data.zip     # License plate detection data
├── traffic_light_data.zip   # Red / Yellow / Green / Unknown / Not Traffic Light
├── test_videos.zip          # Sample test videos
├── plate_labels.csv         # Plate dataset annotations (if CSV format)
└── traffic_light_labels.csv # Traffic light dataset annotations (if CSV format)
```

### Data Preparation

```bash
# Extract and validate all datasets
python scripts/prepare_datasets.py

# Convert VOC/CSV annotations to YOLO format
python scripts/convert_datasets.py
```

### Training Commands

```bash
# Train helmet detection model
python scripts/train.py helmet datasets/helmet_data/data.yaml 100 16 nano

# Train license plate model
python scripts/train.py plate datasets/numberplate_data/data.yaml 100 16 nano

# Train traffic light model
python scripts/train.py traffic_light datasets/traffic_light_data/data.yaml 100 16 nano
```

Arguments: `python scripts/train.py <task> <data_yaml> [epochs] [batch_size] [model_size]`

Model sizes: `nano`, `small`, `medium`

### Export to ONNX

```bash
# Export all models
python scripts/export_models.py

# Export specific model
python scripts/export_models.py helmet
python scripts/export_models.py plate
python scripts/export_models.py traffic_light
```

### Training Results

Training artifacts are saved in `runs/detect/training_runs/`:
- `results.csv` / `results.png` -- Training loss curves
- `confusion_matrix.png` -- Classification accuracy
- `BoxF1_curve.png`, `BoxPR_curve.png` -- Precision/recall metrics
- `weights/best.pt` -- Best model checkpoint

## Model Details

| Model | Classes | Input Size | mAP50 | Size |
|-------|---------|------------|-------|------|
| Helmet Detector | `With Helmet`, `Without Helmet`, `Licence` | 640x640 | 0.855 | 11.7MB |
| Plate Detector | `Plate` (pre-trained) | 640x640 | -- | 11.7MB |
| Traffic Light | `Red`, `Yellow`, `Green`, `Unknown`, `Not Traffic Light` | 640x640 | 0.993 | 11.7MB |

All models are exported to ONNX opset 13 for CPU inference.

## Configuration

### `config/inference.yaml`

```yaml
inference_fps: 10            # Frames per second to process
image_size: 640              # YOLO input resolution
confidence_threshold: 0.45   # Minimum detection confidence
nms_threshold: 0.45          # Non-maximum suppression threshold
device: auto                 # auto, cpu, cuda

helmet_confirmation_frames: 3     # Frames to confirm helmet violation
red_light_confirmation_frames: 3  # Frames to confirm red-light violation
wrong_side_confirmation_frames: 5 # Frames to confirm wrong-side violation
wrong_side_angle_threshold: 150   # Angle threshold for wrong-side detection
```

### `config/violation_rules.yaml`

```yaml
rules:
  NO_HELMET:
    fine_amount: 1000
    active: true
  RED_LIGHT:
    fine_amount: 1000
    active: true
  WRONG_SIDE:
    fine_amount: 1000
    active: true
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEVICE` | `auto` | Compute device (`auto`, `cpu`, `cuda`) |
| `INFERENCE_FPS` | `10` | Processing frame rate |
| `IMAGE_SIZE` | `640` | Model input resolution |
| `CONFIDENCE_THRESHOLD` | `0.45` | Detection confidence threshold |
| `DATABASE_URL` | `sqlite:///ridesafe.db` | Database connection string |
| `API_HOST` | `0.0.0.0` | Server bind address |
| `API_PORT` | `8000` | Server port |

## Architecture

```
                    ┌──────────────────────────────────────────┐
                    │              FastAPI Server               │
                    │         (src/api/main.py :8000)           │
                    └─────────┬──────────────┬─────────────────┘
                              │              │
                    ┌─────────▼───┐  ┌───────▼──────────┐
                    │  Static UI  │  │    REST API       │
                    │ ui/static/  │  │  /api/analyze/*   │
                    └─────────────┘  └───────┬──────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │      ViolationEngine        │
                              │ (violation_engine.py)       │
                              └──┬───────┬───────┬──────┬──┘
                                 │       │       │      │
                    ┌────────────▼┐ ┌────▼────┐ ┌▼─────┐ ┌▼──────────┐
                    │  Helmet     │ │ Plate   │ │Traffic│ │  Tracker  │
                    │  Detector   │ │ Detector│ │Light  │ │ (IoU ReID)│
                    │ (YOLOv8)   │ │ (YOLOv8)│ │Detect │ │           │
                    └──────┬─────┘ └────┬────┘ └──┬───┘ └───────────┘
                           │            │         │
                    ┌──────▼─────┐ ┌────▼────┐ ┌──▼────────────┐
                    │  Helmet    │ │  OCR    │ │ Red-Light /   │
                    │  Violation │ │PaddleOCR│ │ Wrong-Side    │
                    │  Detector  │ │         │ │ Detectors     │
                    └──────┬─────┘ └────┬────┘ └──┬────────────┘
                           │            │         │
                    ┌──────▼────────────▼─────────▼────────────┐
                    │           Evidence Generator              │
                    │   (full frame + vehicle + plate crops)    │
                    └──────────────────┬───────────────────────┘
                                       │
                    ┌──────────────────▼───────────────────────┐
                    │         SQLite / PostgreSQL DB            │
                    │  (Vehicle, Violation, Evidence, Camera)   │
                    └──────────────────────────────────────────┘
```

## Database Schema

- **Vehicle** -- Registered vehicles (plate number, type)
- **Violation** -- Detected violations (type, confidence, fine, status)
- **Evidence** -- Captured evidence (full frame, vehicle crop, plate crop paths)
- **Camera** -- Camera configurations (ROI, stop lines, direction)
- **ViolationRule** -- Fine amounts per violation type

Default: SQLite (`ridesafe.db`). Switch to PostgreSQL by setting `DATABASE_URL`.

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, ONNX Runtime
- **Frontend**: Vanilla HTML/CSS/JS, Chart.js
- **Models**: YOLOv8 (Ultralytics), ONNX opset 13
- **OCR**: PaddleOCR + PaddlePaddle
- **Database**: SQLite (default), PostgreSQL (production)

## License

This project is for educational and research purposes.

## Acknowledgments

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [FastAPI](https://fastapi.tiangolo.com/)
