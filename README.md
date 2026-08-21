# RideSafe AI

Real-time two-wheeler helmet violation detection powered by YOLOv8. Upload images or videos, and the system automatically identifies riders without helmets, draws smart bounding boxes, and generates compliance analytics — all running on CPU with zero database setup.

## Demo

1. Clone and install (see Quick Start below)
2. Run `streamlit run app.py`
3. Upload any image of two-wheeler riders
4. System auto-detects and classifies each rider as compliant (green) or violation (red)

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Rudhrakoushik10/RideSafe_AI.git
cd RideSafe_AI

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the application
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

## Features

- **Auto-Detection** — Upload an image and detection starts automatically, no buttons needed
- **Smart Bounding Boxes** — Green boxes on compliant riders, red highlight on violators
- **Traffic Signal UI** — Intuitive red/amber/green theme for violation severity
- **Analytics Dashboard** — Real-time compliance rate, violation history, session charts
- **Video Support** — Process MP4, AVI, MOV files frame-by-frame with live preview
- **CPU Inference** — ONNX Runtime for lightweight deployment, no GPU required
- **Zero Setup** — In-memory storage, no database installation needed
- **Object Tracking** — IoU-based re-identification across video frames

## How It Works

```
Upload Image/Video
       |
       v
YOLOv8 Detection (ONNX)
       |
       v
Classify: With Helmet / Without Helmet
       |
       v
Smart Bounding Boxes (Green = Compliant, Red = Violation)
       |
       v
Analytics Dashboard (Compliance %, Violation Count, Fines)
```

1. User uploads an image or video via the Streamlit UI
2. YOLOv8 model (ONNX) detects all two-wheeler riders in each frame
3. Each detection is classified as "With Helmet" or "Without Helmet"
4. IoU-based tracker assigns consistent IDs across video frames
5. Smart bounding boxes are drawn: green (compliant) / red (violation)
6. Analytics dashboard updates with compliance stats and violation details

## Project Structure

```
RideSafe_AI/
├── app.py                          # Streamlit application (entry point)
├── config/
│   ├── inference.yaml              # Model paths, thresholds, device settings
│   ├── violation_rules.yaml        # Fine amounts per violation type
│   └── cameras.json                # Camera configurations
├── src/
│   ├── config.py                   # Config loader for YAML/JSON files
│   └── inference/
│       ├── detector.py             # YOLOv8 helmet detector (ONNX Runtime)
│       ├── tracker.py              # IoU-based multi-object tracker
│       ├── helmet_violation.py     # Helmet violation classification logic
│       ├── evidence.py             # Evidence crop generation
│       └── violation_engine.py     # Master inference pipeline
├── src/models/deployment/
│   └── helmet/
│       └── helmet_detector.onnx    # Deployed YOLOv8s model (~43MB)
├── datasets/
│   ├── helmet/                     # Training/validation/test images + labels
│   └── helmet/data_helmet_only.yaml # 2-class training config
├── scripts/
│   ├── train.py                    # YOLOv8 training script with augmentations
│   └── export_models.py            # PyTorch to ONNX export
├── requirements.txt
└── README.md
```

## Model Details

| Property | Value |
|----------|-------|
| Architecture | YOLOv8s (Small) |
| Classes | With Helmet, Without Helmet |
| Training Images | 1,532 (1,069 train / 309 val / 154 test) |
| Epochs | 100 |
| mAP50 | 0.823 |
| With Helmet mAP50 | 0.894 |
| Without Helmet mAP50 | 0.753 |
| Export Format | ONNX Opset 13 |
| Model Size | ~43MB |
| Inference Device | CPU (ONNX Runtime) |

## Configuration

Edit `config/inference.yaml`:

```yaml
inference_fps: 10              # Frames per second for video processing
image_size: 640                # YOLO input resolution
confidence_threshold: 0.45     # Detection confidence (0.05-0.95)
device: cpu                    # cpu (deployment) or cuda (training)
save_evidence: false           # Disable disk I/O for lightweight mode
```

Edit `config/violation_rules.yaml`:

```yaml
rules:
  NO_HELMET:
    fine_amount: 1000          # Fine in INR
    active: true
    description: "Riding two-wheeler without helmet"
```

## Training (GPU Required)

```bash
# Train helmet detector (yolov8s, 100 epochs, GPU)
python scripts/train.py datasets/helmet/data_helmet_only.yaml 100 16 s

# Export trained model to ONNX
python scripts/export_models.py
```

Training uses strong augmentations: rotation (10°), translation (20%), scale (0.9), shear (5°), mixup (0.2), copy-paste (0.3), erasing (0.4).

## Tech Stack

| Component | Technology | Why Chosen |
|-----------|-----------|------------|
| **Object Detection** | YOLOv8s (Ultralytics) | Best speed/accuracy tradeoff for real-time detection; easy training pipeline; native ONNX export support |
| **Model Format** | ONNX Runtime | Enables CPU inference without GPU; smaller deployment footprint; cross-platform compatibility |
| **Web UI** | Streamlit | Rapid prototyping with Python; built-in file upload, metrics, charts; no frontend code needed |
| **Image Processing** | OpenCV | Industry standard for computer vision; efficient bounding box drawing, color space conversion |
| **Numerical Computing** | NumPy | Efficient array operations for bounding box calculations, IoU computation, coordinate transforms |
| **Object Tracking** | IoU-based Tracker | Lightweight multi-object tracking without external dependencies; sufficient for helmet detection use case |
| **Configuration** | PyYAML | Human-readable config files; easy to modify thresholds, paths, rules without code changes |
| **Data Visualization** | Pandas + Streamlit Charts | Session analytics, compliance history, scan results visualization |

### Why CPU Inference?

The system is designed for **edge deployment** on machines without GPU. ONNX Runtime with CPUExecutionProvider provides:
- No CUDA/cuDNN installation required
- ~43MB model size (vs 22MB for GPU models)
- Works on any system with Python 3.8+
- Suitable for deployment on Raspberry Pi, edge servers, or standard laptops

## License

Educational and research purposes.
