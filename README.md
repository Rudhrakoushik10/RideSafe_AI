# RideSafe AI

Real-time two-wheeler helmet violation detection using YOLOv8. Scans images and videos to identify riders without helmets, draws bounding boxes, and generates compliance analytics.

## Quick Start

```bash
git clone https://github.com/Rudhrakoushik10/RideSafe_AI.git
cd RideSafe_AI

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate    # Linux/Mac

pip install -r requirements.txt

streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Features

- **Helmet Detection** -- YOLOv8 classifies riders with/without helmet
- **Smart Bounding Boxes** -- Green boxes on compliant riders, red boxes on violators
- **Object Tracking** -- IoU-based re-identification across video frames
- **Analytics Dashboard** -- Compliance rate, violation history, session charts
- **Video Support** -- Process MP4, AVI, MOV files frame by frame
- **Zero Database** -- All data stored in server memory, no setup required
- **CPU Inference** -- ONNX models for lightweight CPU deployment

## How It Works

1. Upload an image or video
2. YOLOv8 detects all two-wheeler riders in each frame
3. Helmet classifier identifies who is wearing a helmet
4. Bounding boxes drawn: green (compliant) / red (violation)
5. Analytics dashboard updates with compliance stats

## Project Structure

```
RideSafe_AI/
├ app.py                      # Streamlit application (entry point)
├ config/
│   ├ inference.yaml          # Model paths, thresholds, settings
│   ├ violation_rules.yaml    # Fine amounts per violation type
│   └ cameras.json            # Camera configurations
├ src/
│   ├ config.py               # Config loader
│   └ inference/
│       ├ detector.py         # YOLO helmet detector
│       ├ tracker.py          # IoU-based object tracker
│       ├ helmet_violation.py # Helmet violation logic
│       ├ evidence.py         # Evidence crop generation
│       └ violation_engine.py # Master inference pipeline
├ src/models/deployment/      # ONNX model (~12MB)
│   └ helmet/helmet_detector.onnx
├ scripts/                    # Training and export utilities
├ requirements.txt
└ README.md
```

## Model

| Model | Classes | Size |
|-------|---------|------|
| Helmet Detector | With Helmet, Without Helmet | ~12MB |

Exported to ONNX opset 13 for CPU inference.

## Configuration

Edit `config/inference.yaml`:

```yaml
confidence_threshold: 0.45   # Detection confidence (0.05-0.95)
image_size: 640              # YOLO input resolution
device: cpu                  # cpu (deployment)
save_evidence: false         # Disable disk I/O for lightweight mode
```

## Training

```bash
# Train helmet detector (yolov8s, 100 epochs, GPU)
python scripts/train.py datasets/helmet/data_helmet_only.yaml 100 16 s

# Export to ONNX
python scripts/export_models.py
```

## Tech Stack

- **UI**: Streamlit
- **Models**: YOLOv8 (Ultralytics), ONNX Runtime
- **Backend**: Python, OpenCV, NumPy

## License

Educational and research purposes.
