import streamlit as st
import cv2
import numpy as np
from PIL import Image
import tempfile
import time
import os

st.set_page_config(page_title="RideSafe AI", page_icon=":shield:", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0a0e17; }
    [data-testid="stSidebar"] { background-color: #111827; }
    div[data-testid="stMetric"] {
        background: #111827; border: 1px solid #1e293b; border-radius: 10px; padding: 12px;
    }
    div[data-testid="stMetric"] label { color: #64748b !important; font-size: 0.75rem !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #e2e8f0 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 20px; border-radius: 8px; font-weight: 600; }
    .header-banner {
        background: linear-gradient(135deg, #059669 0%, #06b6d4 100%);
        padding: 24px; border-radius: 12px; color: white; text-align: center;
        margin-bottom: 25px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    .header-banner h1 { margin: 0; font-weight: 800; font-size: 2rem; letter-spacing: -0.5px; }
    .header-banner p { margin-top: 8px; font-size: 1rem; opacity: 0.9; }
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
        cv2.rectangle(img, (x1, y1), (x2, y2), (16, 185, 129), 2)
        label = "HELMET OK"
        conf = str(c["confidence"]) + "%"
        (tw, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(img, (x1, y1 - 20), (x1 + tw + 10, y1), (16, 185, 129), -1)
        cv2.putText(img, label, (x1 + 5, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.rectangle(img, (x1, y2), (x1 + 45, y2 + 16), (0, 0, 0), -1)
        cv2.putText(img, conf, (x1 + 4, y2 + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (16, 185, 129), 1, cv2.LINE_AA)

    for v in violations:
        bbox = v.get("bbox")
        if not bbox:
            continue
        x1, y1, x2, y2 = bbox
        overlay = img.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (239, 68, 68), -1)
        cv2.addWeighted(overlay, 0.1, img, 0.9, 0, img)
        cv2.rectangle(img, (x1, y1), (x2, y2), (239, 68, 68), 3)

        label = "NO HELMET"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(img, (x1, y1 - 28), (x1 + tw + 12, y1), (239, 68, 68), -1)
        cv2.putText(img, label, (x1 + 6, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

        conf_text = str(v.get("confidence", 0)) + "%"
        cv2.rectangle(img, (x1, y2), (x1 + 55, y2 + 20), (0, 0, 0), -1)
        cv2.putText(img, conf_text, (x1 + 4, y2 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (239, 68, 68), 1, cv2.LINE_AA)

    return img


def run_detection_on_frame(engine, frame, conf_threshold):
    engine.reset()
    saved_skip = engine.frame_skip
    engine.frame_skip = 1
    engine.confidence_threshold = conf_threshold
    violations_raw = engine.process_frame(frame)
    engine.frame_skip = saved_skip

    all_detections = engine.get_last_detections()
    violation_ids = {v.track_id for v in violations_raw}

    violations = []
    for v in violations_raw:
        violations.append({
            "violation_id": v.violation_id,
            "type": v.violation_type,
            "track_id": v.track_id,
            "plate": v.plate_number or "NOT VISIBLE",
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


def main():
    if "engine" not in st.session_state:
        st.session_state.engine = load_engine()
    if "scan_history" not in st.session_state:
        st.session_state.scan_history = []

    engine = st.session_state.engine

    st.markdown("""
    <div class="header-banner">
        <h1>RideSafe AI</h1>
        <p>Two-wheeler helmet violation detection powered by YOLOv8</p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.title("Settings")
    conf_threshold = st.sidebar.slider("Detection Threshold", 10, 95, 45, 5) / 100.0

    st.sidebar.markdown("---")
    st.sidebar.subheader("Quick Stats")
    history = st.session_state.scan_history
    if history:
        total_scanned = sum(s["scanned"] for s in history)
        total_violations = sum(s["violations"] for s in history)
        total_fines = sum(s["fines"] for s in history)
        st.sidebar.metric("Total Scans", len(history))
        st.sidebar.metric("Riders Scanned", total_scanned)
        st.sidebar.metric("Violations", total_violations)
        st.sidebar.metric("Total Fines", f"Rs.{total_fines:,}")
    else:
        st.sidebar.info("No scans yet.")

    st.sidebar.markdown("---")
    st.sidebar.caption("Helmet: YOLOv8 (mAP50: 0.855)")
    st.sidebar.caption("Plate: YOLOv8 (pre-trained)")
    st.sidebar.caption("Traffic Light: YOLOv8 (mAP50: 0.993)")

    tab_scan, tab_history = st.tabs(["Scan", "Analytics"])

    with tab_scan:
        uploaded = st.file_uploader(
            "Upload image or video",
            type=["jpg", "jpeg", "png", "bmp", "mp4", "avi", "mov"],
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

                start_btn = st.button("Start Video Analysis")

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

                st.image(image_pil, caption=f"Uploaded: {uploaded.name}", use_container_width=True)

                start_btn = st.button("Start Detection")

                if start_btn:
                    with st.spinner("Running detection models..."):
                        violations, compliant = run_detection_on_frame(engine, frame_bgr, conf_threshold)

                    annotated = draw_boxes_on_image(frame_bgr, violations, compliant)
                    st.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), caption="Detection Results", use_container_width=True)

                    _show_results(violations, compliant, uploaded.name)

    with tab_history:
        if not history:
            st.info("Run a scan to see analytics.")
        else:
            import pandas as pd

            total_scanned = sum(s["scanned"] for s in history)
            total_violations = sum(s["violations"] for s in history)
            total_compliant = sum(s["compliant"] for s in history)
            total_fines = sum(s["fines"] for s in history)
            avg_compliance = round(sum(s["compliance"] for s in history) / len(history))

            st.markdown(f"""
            <div style="text-align:center;padding:24px;background:linear-gradient(135deg,#111827,#1a2332);border:1px solid #1e293b;border-radius:12px;margin-bottom:16px;">
                <div style="font-size:48px;font-weight:900;background:linear-gradient(135deg,#10b981,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{avg_compliance}%</div>
                <div style="color:#64748b;font-size:12px;">Average Compliance Rate</div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Scans", len(history))
            c2.metric("Riders Scanned", total_scanned)
            c3.metric("Violations", total_violations)
            c4.metric("Total Fines", f"Rs.{total_fines:,}")

            st.markdown("---")

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
        st.error(f"**{violation_count} rider(s) WITHOUT helmet** -- Total fine: Rs.{total_fines:,}")
    else:
        st.success(f"**All {compliant_count} rider(s) compliant** -- No violations detected")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Scanned", total_scanned)
    m2.metric("Compliant", compliant_count)
    m3.metric("No Helmet", violation_count)
    m4.metric("Total Fine", f"Rs.{total_fines:,}")

    if total_scanned > 0:
        import pandas as pd
        chart_data = pd.DataFrame({
            "Category": ["With Helmet", "No Helmet"],
            "Count": [compliant_count, violation_count],
        })
        st.bar_chart(chart_data.set_index("Category"))
        st.markdown(f"**Compliance Rate: {compliance_rate}%**")
        st.progress(compliance_rate / 100)

    st.markdown("---")

    if violations:
        st.subheader("Violations")
        for v in violations:
            st.markdown(
                f"""<div style="background:#1a0505;border:1px solid #7f1d1d;border-left:3px solid #ef4444;border-radius:8px;padding:12px;margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="color:#ef4444;font-weight:700;">{v['type'].replace('_', ' ')}</span>
                        <span style="color:#ef4444;font-size:11px;background:rgba(239,68,68,.1);padding:2px 8px;border-radius:4px;border:1px solid rgba(239,68,68,.3);">{v['confidence']}%</span>
                    </div>
                    <div style="color:#94a3b8;font-size:11px;margin-top:6px;">
                        Plate: <span style="color:#e2e8f0;font-weight:600;">{v['plate']}</span> |
                        Fine: <span style="color:#ef4444;font-weight:700;">Rs.{v['fine']:,}</span>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

    if compliant:
        st.subheader("Compliant Riders")
        for c in compliant:
            st.markdown(
                f"""<div style="background:#051a0e;border:1px solid #14532d;border-left:3px solid #10b981;border-radius:8px;padding:12px;margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="color:#10b981;font-weight:700;">WITH HELMET</span>
                        <span style="color:#10b981;font-size:11px;background:rgba(16,185,129,.1);padding:2px 8px;border-radius:4px;border:1px solid rgba(16,185,129,.3);">{c['confidence']}%</span>
                    </div>
                    <div style="color:#94a3b8;font-size:11px;margin-top:4px;">Status: <span style="color:#10b981;font-weight:600;">Compliant</span></div>
                </div>""",
                unsafe_allow_html=True,
            )

    if not violations and not compliant:
        st.warning("No riders detected.")


if __name__ == "__main__":
    main()
