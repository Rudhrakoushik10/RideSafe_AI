import streamlit as st
import cv2
import numpy as np
from PIL import Image
import tempfile
import time
import os

st.set_page_config(page_title="RideSafe AI", page_icon="https://img.icons8.com/color/96/traffic-light.png", layout="wide")

TRAFFIC_RED = "#E53935"
TRAFFIC_AMBER = "#FDD835"
TRAFFIC_GREEN = "#43A047"
DARK_BG = "#0d1117"
CARD_BG = "#161b22"
BORDER_COLOR = "#30363d"
TEXT_PRIMARY = "#e6edf3"
TEXT_SECONDARY = "#8b949e"

st.markdown(f"""
<style>
    .stApp {{ background-color: {DARK_BG}; }}
    [data-testid="stSidebar"] {{ background-color: #010409; border-right: 1px solid {BORDER_COLOR}; }}
    div[data-testid="stMetric"] {{
        background: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 10px; padding: 14px;
    }}
    div[data-testid="stMetric"] label {{ color: {TEXT_SECONDARY} !important; font-size: 0.75rem !important; }}
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{ color: {TEXT_PRIMARY} !important; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
    .stTabs [data-baseweb="tab"] {{
        padding: 10px 24px; border-radius: 8px 8px 0 0; font-weight: 600;
        background: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-bottom: none; color: {TEXT_SECONDARY};
    }}
    .stTabs [aria-selected="true"] {{
        background: {CARD_BG} !important; color: {TEXT_PRIMARY} !important;
        border-bottom: 2px solid {TRAFFIC_GREEN} !important;
    }}
    .traffic-header {{
        display: flex; align-items: center; justify-content: center; gap: 20px;
        background: linear-gradient(135deg, #010409 0%, #0d1117 50%, #010409 100%);
        padding: 32px 40px; border-radius: 16px; margin-bottom: 28px;
        border: 1px solid {BORDER_COLOR}; position: relative; overflow: hidden;
    }}
    .traffic-header::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, {TRAFFIC_RED} 0%, {TRAFFIC_RED} 33%, {TRAFFIC_AMBER} 33%, {TRAFFIC_AMBER} 66%, {TRAFFIC_GREEN} 66%, {TRAFFIC_GREEN} 100%);
    }}
    .traffic-light-icon {{
        width: 70px; height: 140px; background: #1c2128; border-radius: 12px;
        border: 2px solid #444c56; display: flex; flex-direction: column;
        align-items: center; justify-content: space-evenly; padding: 10px 0;
        box-shadow: 0 0 20px rgba(0,0,0,0.5); flex-shrink: 0;
    }}
    .light {{ width: 36px; height: 36px; border-radius: 50%; border: 2px solid #30363d; }}
    .light-red {{ background: {TRAFFIC_RED}; box-shadow: 0 0 15px {TRAFFIC_RED}, 0 0 30px rgba(229,57,53,0.3); }}
    .light-amber {{ background: {TRAFFIC_AMBER}; box-shadow: 0 0 15px {TRAFFIC_AMBER}, 0 0 30px rgba(253,216,53,0.3); }}
    .light-green {{ background: {TRAFFIC_GREEN}; box-shadow: 0 0 15px {TRAFFIC_GREEN}, 0 0 30px rgba(67,160,71,0.3); }}
    .header-text h1 {{
        margin: 0; font-size: 2.2rem; font-weight: 800; letter-spacing: -0.5px; color: {TEXT_PRIMARY};
    }}
    .header-text h1 span {{ color: {TRAFFIC_GREEN}; }}
    .header-text p {{ margin-top: 8px; font-size: 1rem; color: {TEXT_SECONDARY}; }}
    .header-text .tag {{
        display: inline-block; margin-top: 10px; padding: 4px 12px; border-radius: 20px;
        font-size: 0.7rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;
        background: rgba(67,160,71,0.15); color: {TRAFFIC_GREEN}; border: 1px solid rgba(67,160,71,0.3);
    }}
    .status-badge {{
        display: inline-block; padding: 6px 16px; border-radius: 8px; font-weight: 700;
        font-size: 0.95rem; margin-bottom: 12px;
    }}
    .badge-violation {{ background: rgba(229,57,53,0.15); color: {TRAFFIC_RED}; border: 1px solid rgba(229,57,53,0.3); }}
    .badge-safe {{ background: rgba(67,160,71,0.15); color: {TRAFFIC_GREEN}; border: 1px solid rgba(67,160,71,0.3); }}
    .badge-detecting {{ background: rgba(253,216,53,0.15); color: {TRAFFIC_AMBER}; border: 1px solid rgba(253,216,53,0.3); }}
    .violation-card {{
        background: #1a0a0a; border: 1px solid #5c1d1d; border-left: 4px solid {TRAFFIC_RED};
        border-radius: 10px; padding: 14px 16px; margin-bottom: 10px;
    }}
    .violation-card .title {{ color: {TRAFFIC_RED}; font-weight: 700; font-size: 0.95rem; }}
    .violation-card .meta {{ color: {TEXT_SECONDARY}; font-size: 0.8rem; margin-top: 6px; }}
    .violation-card .fine {{ color: {TRAFFIC_RED}; font-weight: 700; }}
    .compliant-card {{
        background: #0a1a0e; border: 1px solid #1a4028; border-left: 4px solid {TRAFFIC_GREEN};
        border-radius: 10px; padding: 14px 16px; margin-bottom: 10px;
    }}
    .compliant-card .title {{ color: {TRAFFIC_GREEN}; font-weight: 700; font-size: 0.95rem; }}
    .compliant-card .meta {{ color: {TEXT_SECONDARY}; font-size: 0.8rem; margin-top: 4px; }}
    .upload-zone {{
        border: 2px dashed {BORDER_COLOR}; border-radius: 16px; padding: 48px 24px;
        text-align: center; background: {CARD_BG}; transition: border-color 0.3s;
    }}
    .upload-zone:hover {{ border-color: {TRAFFIC_GREEN}; }}
    .result-bar {{
        display: flex; gap: 0; border-radius: 10px; overflow: hidden; height: 8px; margin: 16px 0;
    }}
    .bar-green {{ background: {TRAFFIC_GREEN}; }}
    .bar-red {{ background: {TRAFFIC_RED}; }}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_engine():
    from src.config import load_config
    from src.inference.violation_engine import ViolationEngine
    config = load_config()
    config["save_evidence"] = False
    engine = ViolationEngine(config)
    return engine


def draw_boxes_on_image(frame, violations, compliant):
    img = frame.copy()
    for c in compliant:
        x1, y1, x2, y2 = c["bbox"]
        cv2.rectangle(img, (x1, y1), (x2, y2), (67, 160, 71), 2)
        label = "HELMET OK"
        conf = str(c["confidence"]) + "%"
        (tw, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(img, (x1, y1 - 20), (x1 + tw + 10, y1), (67, 160, 71), -1)
        cv2.putText(img, label, (x1 + 5, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.rectangle(img, (x1, y2), (x1 + 45, y2 + 16), (0, 0, 0), -1)
        cv2.putText(img, conf, (x1 + 4, y2 + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (67, 160, 71), 1, cv2.LINE_AA)

    for v in violations:
        bbox = v.get("bbox")
        if not bbox:
            continue
        x1, y1, x2, y2 = bbox
        overlay = img.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (229, 57, 53), -1)
        cv2.addWeighted(overlay, 0.1, img, 0.9, 0, img)
        cv2.rectangle(img, (x1, y1), (x2, y2), (229, 57, 53), 3)
        label = "NO HELMET"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(img, (x1, y1 - 28), (x1 + tw + 12, y1), (229, 57, 53), -1)
        cv2.putText(img, label, (x1 + 6, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        conf_text = str(v.get("confidence", 0)) + "%"
        cv2.rectangle(img, (x1, y2), (x1 + 55, y2 + 20), (0, 0, 0), -1)
        cv2.putText(img, conf_text, (x1 + 4, y2 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (229, 57, 53), 1, cv2.LINE_AA)

    return img


def run_detection_on_frame(engine, frame, conf_threshold):
    engine.reset()
    saved_skip = engine.frame_skip
    saved_confirm = engine.helmet_violation.confirmation_frames
    engine.frame_skip = 1
    engine.helmet_violation.confirmation_frames = 1
    engine.confidence_threshold = conf_threshold
    violations_raw = engine.process_frame(frame)
    engine.frame_skip = saved_skip
    engine.helmet_violation.confirmation_frames = saved_confirm

    all_detections = engine.get_last_detections()
    violation_ids = {v.track_id for v in violations_raw}

    violations = []
    for v in violations_raw:
        violations.append({
            "violation_id": v.violation_id,
            "type": v.violation_type,
            "track_id": v.track_id,
            "plate": "N/A",
            "confidence": round(v.confidence * 100),
            "fine": v.fine_amount,
            "bbox": v.evidence.get("metadata", {}).get("bbox") if v.evidence else None,
        })

    compliant = []
    for det in all_detections:
        if det.get("track_id") not in violation_ids:
            compliant.append({
                "track_id": det.get("track_id"),
                "bbox": det["bbox"],
                "confidence": round(det["confidence"] * 100),
            })

    return violations, compliant


def _render_traffic_light(size="large"):
    if size == "large":
        return """
        <div class="traffic-light-icon">
            <div class="light light-red"></div>
            <div class="light light-amber"></div>
            <div class="light light-green"></div>
        </div>
        """
    return '<span style="font-size:1.2rem;">&#128678;</span>'


def main():
    if "engine" not in st.session_state:
        st.session_state.engine = load_engine()
    if "scan_history" not in st.session_state:
        st.session_state.scan_history = []

    engine = st.session_state.engine

    st.markdown(f"""
    <div class="traffic-header">
        {_render_traffic_light("large")}
        <div class="header-text">
            <h1>Ride<span>Safe</span> AI</h1>
            <p>Two-wheeler helmet violation detection powered by YOLOv8</p>
            <span class="tag">Real-time Analysis</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center;padding:16px 0 8px 0;">
            <div style="font-size:1.5rem;font-weight:800;color:{TEXT_PRIMARY};">RideSafe</div>
            <div style="font-size:0.7rem;color:{TEXT_SECONDARY};text-transform:uppercase;letter-spacing:2px;">Control Panel</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<hr style="border-color:{BORDER_COLOR};">', unsafe_allow_html=True)

        conf_threshold = st.slider("Detection Threshold", 10, 95, 45, 5) / 100.0

        st.markdown(f'<hr style="border-color:{BORDER_COLOR};">', unsafe_allow_html=True)

        st.markdown(f'<div style="color:{TEXT_SECONDARY};font-size:0.7rem;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;margin-bottom:12px;">Session Analytics</div>', unsafe_allow_html=True)
        history = st.session_state.scan_history
        if history:
            total_scanned = sum(s["scanned"] for s in history)
            total_violations = sum(s["violations"] for s in history)
            total_fines = sum(s["fines"] for s in history)
            total_compliant = total_scanned - total_violations
            avg_compliance = round(sum(s["compliance"] for s in history) / len(history))

            st.metric("Total Scans", len(history))
            st.metric("Riders Scanned", total_scanned)
            st.metric("Violations", total_violations, delta=f"{total_violations} detected", delta_color="off")
            st.metric("Total Fines", f"Rs.{total_fines:,}")
        else:
            st.info("No scans yet.")

        st.markdown(f'<hr style="border-color:{BORDER_COLOR};">', unsafe_allow_html=True)

        st.markdown(f"""
        <div style="padding:8px 0;">
            <div style="color:{TEXT_SECONDARY};font-size:0.65rem;text-transform:uppercase;letter-spacing:1px;">Model</div>
            <div style="color:{TEXT_PRIMARY};font-size:0.8rem;margin-top:4px;">YOLOv8 Helmet Detector</div>
            <div style="color:{TEXT_SECONDARY};font-size:0.65rem;margin-top:2px;">ONNX Runtime | CPU Inference</div>
        </div>
        """, unsafe_allow_html=True)

    tab_scan, tab_history = st.tabs(["Scan", "Analytics"])

    with tab_scan:
        uploaded = st.file_uploader(
            "Upload image or video",
            type=["jpg", "jpeg", "png", "bmp", "mp4", "avi", "mov"],
            label_visibility="collapsed",
        )

        if uploaded is not None:
            file_bytes = uploaded.read()
            is_video = uploaded.type.startswith("video")

            if is_video:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded.name.split('.')[-1]}") as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name

                cap = cv2.VideoCapture(tmp_path)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

                st.markdown(f"""
                <div style="background:{CARD_BG};border:1px solid {BORDER_COLOR};border-radius:12px;padding:16px 20px;margin-bottom:16px;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="width:10px;height:10px;border-radius:50%;background:{TRAFFIC_AMBER};box-shadow:0 0 8px {TRAFFIC_AMBER};"></div>
                        <div>
                            <div style="color:{TEXT_PRIMARY};font-weight:600;font-size:0.95rem;">{uploaded.name}</div>
                            <div style="color:{TEXT_SECONDARY};font-size:0.8rem;">{width}x{height} | {total_frames} frames | Video</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                start_btn = st.button("Start Video Analysis", type="primary", use_container_width=True)

                if start_btn:
                    progress_bar = st.progress(0.0)
                    status_text = st.empty()
                    live_preview = st.empty()

                    all_violations = {}
                    all_compliant = {}
                    frame_idx = 0

                    while cap.isOpened():
                        ret, frame = cap.read()
                        if not ret:
                            break
                        frame_idx += 1
                        violations, compliant = run_detection_on_frame(engine, frame, conf_threshold)

                        for v in violations:
                            key = v["track_id"]
                            if key not in all_violations or v["confidence"] > all_violations[key]["confidence"]:
                                all_violations[key] = v
                        for c in compliant:
                            key = c["track_id"]
                            if key not in all_compliant or c["confidence"] > all_compliant[key]["confidence"]:
                                all_compliant[key] = c

                        if frame_idx % 3 == 0 or frame_idx == total_frames:
                            progress = min(1.0, frame_idx / total_frames)
                            progress_bar.progress(progress)
                            status_text.text(f"Processing frame {frame_idx}/{total_frames} ({int(progress*100)}%)")

                            annotated = draw_boxes_on_image(frame, list(all_violations.values()), list(all_compliant.values()))
                            live_preview.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), caption=f"Frame {frame_idx}", use_container_width=True)

                    cap.release()
                    os.unlink(tmp_path)
                    progress_bar.progress(1.0)
                    status_text.success("Video analysis complete!")

                    violations_list = list(all_violations.values())
                    compliant_list = list(all_compliant.values())
                    _show_results(violations_list, compliant_list, uploaded.name)

            else:
                image_pil = Image.open(uploaded).convert("RGB")
                frame_bgr = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

                with st.spinner("Analyzing..."):
                    violations, compliant = run_detection_on_frame(engine, frame_bgr, conf_threshold)

                annotated = draw_boxes_on_image(frame_bgr, violations, compliant)
                st.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), caption=f"Uploaded: {uploaded.name}", use_container_width=True)

                _show_results(violations, compliant, uploaded.name)

    with tab_history:
        if not history:
            st.markdown(f"""
            <div style="text-align:center;padding:60px 20px;">
                <div style="font-size:3rem;margin-bottom:16px;">&#128678;</div>
                <div style="color:{TEXT_PRIMARY};font-size:1.1rem;font-weight:600;">No scans yet</div>
                <div style="color:{TEXT_SECONDARY};font-size:0.85rem;margin-top:8px;">Upload an image to get started</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            import pandas as pd

            total_scanned = sum(s["scanned"] for s in history)
            total_violations = sum(s["violations"] for s in history)
            total_compliant = sum(s["compliant"] for s in history)
            total_fines = sum(s["fines"] for s in history)
            avg_compliance = round(sum(s["compliance"] for s in history) / len(history))

            st.markdown(f"""
            <div style="text-align:center;padding:28px;background:{CARD_BG};border:1px solid {BORDER_COLOR};border-radius:14px;margin-bottom:20px;">
                <div style="font-size:52px;font-weight:900;background:linear-gradient(135deg,{TRAFFIC_GREEN},{TRAFFIC_AMBER});-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{avg_compliance}%</div>
                <div style="color:{TEXT_SECONDARY};font-size:12px;letter-spacing:1px;text-transform:uppercase;">Average Compliance Rate</div>
                <div style="height:4px;background:{BORDER_COLOR};border-radius:2px;margin:16px 40px 0 40px;overflow:hidden;">
                    <div style="width:{avg_compliance}%;height:100%;background:linear-gradient(90deg,{TRAFFIC_GREEN},{TRAFFIC_AMBER});border-radius:2px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Scans", len(history))
            c2.metric("Riders Scanned", total_scanned)
            c3.metric("Violations", total_violations)
            c4.metric("Total Fines", f"Rs.{total_fines:,}")

            st.markdown(f'<hr style="border-color:{BORDER_COLOR};">', unsafe_allow_html=True)

            df = pd.DataFrame(history)
            col_chart, col_table = st.columns([1, 1])

            with col_chart:
                st.subheader("Scan Results")
                st.bar_chart(df.set_index("file")[["compliant", "violations"]])

            with col_table:
                st.subheader("Scan History")
                st.dataframe(
                    df[["file", "time", "scanned", "compliant", "violations", "fines", "compliance"]],
                    use_container_width=True, hide_index=True,
                )


def _show_results(violations, compliant, filename):
    total_scanned = len(violations) + len(compliant)
    violation_count = len(violations)
    compliant_count = len(compliant)
    total_fines = sum(v["fine"] for v in violations)
    compliance_rate = round((compliant_count / total_scanned) * 100) if total_scanned > 0 else 100

    st.session_state.scan_history.append({
        "file": filename,
        "time": time.strftime("%H:%M:%S"),
        "date": time.strftime("%Y-%m-%d"),
        "scanned": total_scanned,
        "compliant": compliant_count,
        "violations": violation_count,
        "fines": total_fines,
        "compliance": compliance_rate,
    })

    if violation_count > 0:
        badge_cls = "badge-violation"
        badge_text = f"{violation_count} VIOLATION{'S' if violation_count > 1 else ''} DETECTED"
        summary = f"Total fine: Rs.{total_fines:,}"
    else:
        badge_cls = "badge-safe"
        badge_text = "ALL RIDERS COMPLIANT"
        summary = f"All {compliant_count} rider(s) wearing helmet"

    st.markdown(f"""
    <div class="status-badge {badge_cls}">{badge_text}</div>
    <div style="color:{TEXT_SECONDARY};font-size:0.85rem;margin-bottom:16px;">{summary}</div>
    """, unsafe_allow_html=True)

    if total_scanned > 0:
        green_w = max(2, compliance_rate)
        red_w = max(2, 100 - compliance_rate)
        st.markdown(f"""
        <div class="result-bar">
            <div class="bar-green" style="width:{green_w}%;"></div>
            <div class="bar-red" style="width:{red_w}%;"></div>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
            <span style="color:{TRAFFIC_GREEN};font-size:0.75rem;font-weight:600;">Compliant {compliance_rate}%</span>
            <span style="color:{TRAFFIC_RED};font-size:0.75rem;font-weight:600;">Violations {100 - compliance_rate}%</span>
        </div>
        """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Scanned", total_scanned)
    m2.metric("Compliant", compliant_count)
    m3.metric("No Helmet", violation_count)
    m4.metric("Total Fine", f"Rs.{total_fines:,}")

    st.markdown(f'<hr style="border-color:{BORDER_COLOR};">', unsafe_allow_html=True)

    if violations:
        st.markdown(f'<div style="color:{TRAFFIC_RED};font-size:0.75rem;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;margin-bottom:10px;">Violations</div>', unsafe_allow_html=True)
        for v in violations:
            st.markdown(
                f"""<div class="violation-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span class="title">{v['type'].replace('_', ' ')}</span>
                        <span style="color:{TRAFFIC_RED};font-size:0.7rem;background:rgba(229,57,53,.1);padding:2px 8px;border-radius:4px;border:1px solid rgba(229,57,53,.3);">{v['confidence']}%</span>
                    </div>
                    <div class="meta">
                        Fine: <span class="fine">Rs.{v['fine']:,}</span>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

    if compliant:
        st.markdown(f'<div style="color:{TRAFFIC_GREEN};font-size:0.75rem;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;margin-bottom:10px;">Compliant Riders</div>', unsafe_allow_html=True)
        for c in compliant:
            st.markdown(
                f"""<div class="compliant-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span class="title">WITH HELMET</span>
                        <span style="color:{TRAFFIC_GREEN};font-size:0.7rem;background:rgba(67,160,71,.1);padding:2px 8px;border-radius:4px;border:1px solid rgba(67,160,71,.3);">{c['confidence']}%</span>
                    </div>
                    <div class="meta">Status: <span style="color:{TRAFFIC_GREEN};font-weight:600;">Compliant</span></div>
                </div>""",
                unsafe_allow_html=True,
            )

    if not violations and not compliant:
        st.warning("No riders detected.")


if __name__ == "__main__":
    main()
