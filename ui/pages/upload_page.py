import streamlit as st
import time
import base64
import io
import sys
from lib.api_client import health_check, analyze_image, analyze_video, get_evidence_url
from lib.simulator import inject_simulated_red_light, make_violation_from_api_result, PLATE_NOT_VISIBLE
from lib.types import VehicleDetection, ViolationRecord, Evidence, OCRConfidence, OCRCharacter
from lib.mock_data import FINE_AMOUNTS, LAW_SECTIONS


def _run_analysis():
    st.session_state.analysis_running = True
    st.session_state.analysis_complete = False
    st.session_state.detections = []
    st.session_state.analysis_progress = 0


def _finish_analysis(api_results: list, evidence_urls: dict):
    st.session_state.analysis_running = False
    st.session_state.analysis_complete = True

    violations = []
    for result in api_results:
        vid = result.get("violation_id", "")
        ev_full = evidence_urls.get(vid, {}).get("full_frame", "")
        ev_crop = evidence_urls.get(vid, {}).get("vehicle_crop", "")
        vio = make_violation_from_api_result(result, ev_full, ev_crop)
        violations.append(vio)
        st.session_state.violations.insert(0, vio)

    sim_rl = inject_simulated_red_light(violations)
    if sim_rl:
        violations.append(sim_rl)
        st.session_state.violations.insert(0, sim_rl)

    st.session_state.api_violations = violations

    detections = []
    for result in api_results:
        vtype = result.get("violation_type", "")
        plate = result.get("plate_number")
        detections.append(VehicleDetection(
            id=f"det-{result.get('violation_id', 'x')}",
            tracking_id=f"TRK-#{result.get('track_id', 0)}",
            vehicle_type="Two-Wheeler",
            model="",
            plate_number=plate if plate else PLATE_NOT_VISIBLE,
            confidence=result.get("confidence", 0),
            helmet_status="NOT_DETECTED" if vtype == "NO_HELMET" else "DETECTED",
            speed_kmh=0,
            direction="UNKNOWN",
            is_violating=True,
            violation_type=vtype,
            box={},
            head_box=None,
            plate_box=None,
        ))
    st.session_state.detections = detections

    if sim_rl:
        st.session_state.detections.append(VehicleDetection(
            id="det-sim-rl",
            tracking_id="TRK-#SIM",
            vehicle_type="Two-Wheeler",
            model="",
            plate_number=sim_rl.plate_number,
            confidence=sim_rl.confidence,
            helmet_status="DETECTED",
            speed_kmh=sim_rl.speed_kmh,
            direction="UNKNOWN",
            is_violating=True,
            violation_type="RED_LIGHT",
            box={},
            head_box=None,
            plate_box=None,
        ))


def render():
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:12px;border-bottom:1px solid #182338;padding-bottom:12px;">
                <div>
                    <h1 style="font-size:1.5rem;font-weight:900;color:white;letter-spacing:-0.02em;font-family:monospace;margin:0;">
                        AI Vision Lab
                        <span style="font-size:10px;font-weight:700;padding:2px 8px;border-radius:20px;background:rgba(16,185,129,0.15);color:#34d399;border:1px solid rgba(16,185,129,0.3);margin-left:8px;">ACTIVE</span>
                    </h1>
                    <p style="font-size:12px;color:#94a3b8;margin:4px 0 0 0;font-family:monospace;">
                        Automated computer-vision for <strong style="color:#f87171;">No-Helmet</strong>, <strong style="color:#fbbf24;">Red-Light Stopline</strong>, and <strong style="color:#f87171;">Wrong-Side</strong> infractions.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_h2:
        api_ok = health_check()
        if api_ok:
            st.markdown(
                '<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;font-family:monospace;color:#34d399;">'
                '<span class="dot-green"></span> Backend Online</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;font-family:monospace;color:#f87171;">'
                '<span class="dot-red"></span> Backend Offline</span>',
                unsafe_allow_html=True,
            )

    if st.session_state.uploaded_media:
        with col_h2:
            if st.button("New File", use_container_width=True):
                st.session_state.uploaded_media = None
                st.session_state.analysis_running = False
                st.session_state.analysis_complete = False
                st.session_state.detections = []
                st.rerun()

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    if not st.session_state.uploaded_media:
        _render_upload_screen()
    else:
        _render_analysis_screen()


def _render_upload_screen():
    st.markdown(
        """
        <div style="max-width:640px;margin:24px auto;">
            <div style="border:2px dashed #1e2a40;border-radius:16px;padding:48px 40px;text-align:center;
                        background:#090d16;display:flex;flex-direction:column;align-items:center;gap:16px;">
                <div style="display:flex;align-items:center;gap:12px;padding:12px;border-radius:16px;
                            background:#0c121e;border:1px solid #1b263c;">
                    <div style="display:inline-flex;flex-direction:column;align-items:center;justify-content:space-between;
                                background:#0b0f19;border:1px solid #334155;border-radius:6px;padding:4px;gap:3px;
                                box-shadow:0 4px 12px rgba(0,0,0,0.8);width:24px;height:64px;">
                        <div style="width:10px;height:10px;border-radius:50%;background:#ef4444;box-shadow:0 0 8px #ef4444;"></div>
                        <div style="width:10px;height:10px;border-radius:50%;background:#f59e0b;box-shadow:0 0 8px #f59e0b;"></div>
                        <div style="width:10px;height:10px;border-radius:50%;background:#10b981;box-shadow:0 0 8px #10b981;"></div>
                    </div>
                    <div style="font-family:monospace;text-align:left;">
                        <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;">Ready for Ingestion</div>
                        <div style="font-size:12px;font-weight:700;color:#34d399;display:flex;align-items:center;gap:4px;">
                            <span style="width:6px;height:6px;border-radius:50%;background:#34d399;" class="pulse-anim"></span>
                            YOLOv8 Detection Core Ready
                        </div>
                    </div>
                </div>
                <div>
                    <div style="font-size:1.1rem;font-weight:700;color:white;font-family:sans-serif;">
                        Upload Traffic Photo or Video Frame
                    </div>
                    <div style="font-size:12px;color:#94a3b8;margin-top:4px;font-family:monospace;">
                        Drag and drop your media file here, or click to browse
                    </div>
                    <div style="font-size:11px;color:#64748b;margin-top:2px;font-family:monospace;">
                        Supports JPG, PNG, MP4, WebM - High-Resolution ANPR & Helmet Analysis
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload traffic image or video",
        type=["jpg", "jpeg", "png", "mp4", "webm", "avi"],
        label_visibility="collapsed",
        key="file_upload_main",
    )

    st.markdown(
        '<div style="text-align:center;margin-top:-8px;"><span style="font-size:11px;color:#64748b;font-family:monospace;">or use the upload area above</span></div>',
        unsafe_allow_html=True,
    )

    if uploaded_file:
        is_video = uploaded_file.type.startswith("video")
        file_bytes = uploaded_file.read()
        b64 = base64.b64encode(file_bytes).decode()
        mime = uploaded_file.type

        data_url = f"data:{mime};base64,{b64}"

        st.session_state.uploaded_media = {
            "file_name": uploaded_file.name,
            "file_type": "video" if is_video else "image",
            "url": data_url,
            "file_bytes": file_bytes,
            "local_file": uploaded_file,
        }
        st.session_state.analysis_running = False
        st.session_state.analysis_complete = False
        st.session_state.detections = []
        st.rerun()

    st.markdown(
        """
        <div style="max-width:640px;margin:24px auto 0;">
            <div style="padding:16px;border-radius:16px;background:#090d16;border:1px solid #182338;font-family:monospace;font-size:12px;">
                <div style="font-weight:700;color:white;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:12px;
                            display:flex;align-items:center;gap:8px;">
                    <span style="color:#f59e0b;">Traffic Signal AI Verification Rules</span>
                </div>
                <div style="display:flex;flex-direction:column;gap:8px;">
                    <div style="padding:10px;border-radius:12px;background:#0c121e;border:1px solid rgba(239,68,68,0.3);
                                display:flex;align-items:flex-start;gap:8px;">
                        <span style="width:8px;height:8px;border-radius:50%;background:#ef4444;margin-top:4px;flex-shrink:0;"></span>
                        <div>
                            <strong style="color:#f87171;font-weight:600;">1. No Helmet Infraction:</strong>
                            <span style="color:#94a3b8;"> Detects riders without certified safety helmets in high-density corridors.</span>
                        </div>
                    </div>
                    <div style="padding:10px;border-radius:12px;background:#0c121e;border:1px solid rgba(245,158,11,0.3);
                                display:flex;align-items:flex-start;gap:8px;">
                        <span style="width:8px;height:8px;border-radius:50%;background:#f59e0b;margin-top:4px;flex-shrink:0;"></span>
                        <div>
                            <strong style="color:#fbbf24;font-weight:600;">2. Red Light Signal Breach:</strong>
                            <span style="color:#94a3b8;"> Flags stop-line cross-overs during red signal clearance phase. <em style="color:#fbbf24;">(Simulated)</em></span>
                        </div>
                    </div>
                    <div style="padding:10px;border-radius:12px;background:#0c121e;border:1px solid rgba(239,68,68,0.3);
                                display:flex;align-items:flex-start;gap:8px;">
                        <span style="width:8px;height:8px;border-radius:50%;background:#ef4444;margin-top:4px;flex-shrink:0;"></span>
                        <div>
                            <strong style="color:#f87171;font-weight:600;">3. Wrong-Side Contraflow:</strong>
                            <span style="color:#94a3b8;"> Identifies dangerous opposing-direction travel against traffic flow.</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_analysis_screen():
    media = st.session_state.uploaded_media
    if not media:
        return

    left, right = st.columns([7, 5])

    with left:
        st.markdown(
            f"""
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;font-family:monospace;font-size:12px;">
                <span style="color:#94a3b8;">Evidence: <strong style="color:white;">{media['file_name']}</strong></span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if media["file_type"] == "video":
            st.video(media["local_file"])
        else:
            st.image(media["url"], use_container_width=True)

        if not st.session_state.analysis_running and not st.session_state.analysis_complete:
            api_ok = health_check()
            if not api_ok:
                st.markdown(
                    '<div style="padding:10px;border-radius:8px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);'
                    'font-family:monospace;font-size:12px;color:#f87171;">'
                    'Backend API is not running. Start it with: <code>uvicorn src.api.main:app --port 8000</code></div>',
                    unsafe_allow_html=True,
                )
            else:
                if st.button("Run AI Detection (Analyze Signals)", use_container_width=True, type="primary"):
                    _run_analysis()
                    st.rerun()

    with right:
        if st.session_state.analysis_running:
            _render_analyzing_state()
        elif st.session_state.analysis_complete:
            _render_results()
        else:
            _render_idle_instructions()


def _render_analyzing_state():
    progress = st.session_state.get("analysis_progress", 0)
    media = st.session_state.uploaded_media

    st.markdown(
        f"""
        <div style="text-align:center;padding:24px;">
            <div style="display:inline-flex;flex-direction:column;align-items:center;justify-content:space-between;
                        background:#0b0f19;border:1px solid #334155;border-radius:6px;padding:4px;gap:3px;
                        box-shadow:0 4px 12px rgba(0,0,0,0.8);width:24px;height:64px;margin:0 auto 16px;">
                <div style="width:10px;height:10px;border-radius:50%;background:#ef4444;box-shadow:0 0 8px #ef4444;"></div>
                <div style="width:10px;height:10px;border-radius:50%;background:#f59e0b;box-shadow:0 0 8px #f59e0b;"></div>
                <div style="width:10px;height:10px;border-radius:50%;background:#10b981;box-shadow:0 0 8px #10b981;"></div>
            </div>
            <div style="font-size:12px;font-weight:700;color:white;font-family:monospace;">Analyzing Signal Safety...</div>
            <div style="margin:12px 0;background:#141d31;border-radius:8px;height:6px;overflow:hidden;width:200px;margin-left:auto;margin-right:auto;">
                <div style="height:100%;background:#10b981;box-shadow:0 0 8px #10b981;width:{progress}%;transition:width 0.3s;border-radius:8px;"></div>
            </div>
            <div style="font-size:10px;font-family:monospace;color:#fbbf24;">Running YOLOv8 Detection Core...</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    bar = st.progress(progress / 100)
    status_text = st.empty()

    for p in range(progress + 1, 51, 3):
        time.sleep(0.03)
        bar.progress(p / 100)
        status_text.markdown(
            '<span style="font-family:monospace;font-size:11px;color:#fbbf24;">Running YOLOv8 Detection Core...</span>',
            unsafe_allow_html=True,
        )
        st.session_state.analysis_progress = p

    bar.progress(0.5)
    status_text.markdown(
        '<span style="font-family:monospace;font-size:11px;color:#fbbf24;">Sending to backend for inference...</span>',
        unsafe_allow_html=True,
    )

    try:
        file_bytes = media["file_bytes"]
        filename = media["file_name"]

        if media["file_type"] == "image":
            response = analyze_image(file_bytes, filename)
        else:
            response = analyze_video(file_bytes, filename)

        api_violations = response.get("violations", [])
        evidence_urls = {}
        for v in api_violations:
            vid = v.get("violation_id", "")
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            evidence_urls[vid] = {
                "full_frame": f"http://localhost:8000/api/evidence/{today}/{vid}/full_frame.jpg",
                "vehicle_crop": f"http://localhost:8000/api/evidence/{today}/{vid}/vehicle_crop.jpg",
            }

    except Exception as e:
        api_violations = []
        evidence_urls = {}
        st.session_state._api_error = str(e)

    for p in range(51, 101, 5):
        time.sleep(0.02)
        bar.progress(p / 100)
        step = "Classifying helmet status..." if p < 75 else "Generating evidence crops..."
        status_text.markdown(
            f'<span style="font-family:monospace;font-size:11px;color:#fbbf24;">{step}</span>',
            unsafe_allow_html=True,
        )
        st.session_state.analysis_progress = p

    bar.progress(1.0)
    status_text.markdown(
        '<span style="font-family:monospace;font-size:11px;color:#34d399;">Analysis Complete!</span>',
        unsafe_allow_html=True,
    )
    time.sleep(0.3)

    if api_violations:
        _finish_analysis(api_violations, evidence_urls)
    else:
        st.session_state.analysis_running = False
        st.session_state.analysis_complete = True
        st.session_state.detections = []
        st.session_state.api_violations = []
        if "_api_error" in st.session_state:
            st.session_state._analysis_error = st.session_state._api_error
            del st.session_state._api_error

    st.session_state.analysis_progress = 0
    st.rerun()


def _render_results():
    detections = st.session_state.detections
    api_violations = st.session_state.get("api_violations", [])

    moto_count = max(len(detections), 1)
    vio_count = len([d for d in detections if d.is_violating])
    compliant = sum(1 for d in detections if d.helmet_status == "DETECTED")
    compliance = round((compliant / moto_count * 100) if moto_count > 0 else 100)

    error_msg = st.session_state.pop("_analysis_error", None)
    if error_msg:
        st.markdown(
            f'<div style="padding:10px;border-radius:8px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);'
            f'font-family:monospace;font-size:12px;color:#f87171;margin-bottom:12px;">'
            f'Analysis error: {error_msg}</div>',
            unsafe_allow_html=True,
        )

    if not detections:
        st.markdown(
            """
            <div style="padding:32px;text-align:center;border-radius:16px;background:#090d16;border:1px solid #182338;">
                <div style="font-size:2rem;margin-bottom:8px;">&#10003;</div>
                <div style="font-size:14px;font-weight:700;color:white;font-family:monospace;">No Violations Detected</div>
                <p style="font-size:12px;color:#94a3b8;font-family:monospace;margin-top:4px;">
                    All vehicles in the frame are compliant with traffic regulations.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:12px;">
            <div class="kpi-amber">
                <div class="mini-metric-label" style="color:#fbbf24;">Two-Wheelers</div>
                <div style="font-size:1.25rem;font-weight:900;color:white;font-family:monospace;">{moto_count}</div>
            </div>
            <div class="kpi-red">
                <div class="mini-metric-label" style="color:#f87171;">Infractions</div>
                <div style="font-size:1.25rem;font-weight:900;color:#f87171;font-family:monospace;">{vio_count}</div>
            </div>
            <div class="kpi-green">
                <div class="mini-metric-label" style="color:#34d399;">Compliance</div>
                <div style="font-size:1.25rem;font-weight:900;color:#34d399;font-family:monospace;">{compliance}%</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if any(v.type == "RED_LIGHT" and "SIMULATED" in v.notes for v in api_violations):
        st.markdown(
            '<div style="padding:10px;border-radius:8px;background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);'
            'font-family:monospace;font-size:11px;color:#fbbf24;margin-bottom:12px;display:flex;align-items:center;gap:8px;">'
            '<span class="dot-amber"></span> <strong>SIMULATED:</strong> Red-light violations are programmatically generated for demo. '
            'No stop-line ROI configured for this camera.</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="section-title" style="margin-bottom:8px;">Detected Two-Wheelers:</div>',
        unsafe_allow_html=True,
    )

    for idx, det in enumerate(detections):
        is_vio = det.is_violating
        border_color = "rgba(239,68,68,0.5)" if is_vio else "rgba(16,185,129,0.3)"
        bg_color = "#101422" if is_vio else "#090d16"
        status_text = det.violation_type.replace("_", " ") if is_vio else "COMPLIANT (SAFE)"
        badge_cls = "badge-red" if is_vio else "badge-green"
        dot_cls = "dot-red" if is_vio else "dot-green"
        fine_text = f"Rs.{FINE_AMOUNTS.get(det.violation_type, 1000):,}" if is_vio else ""

        is_sim = det.violation_type == "RED_LIGHT"
        plate_display = det.plate_number
        if plate_display == PLATE_NOT_VISIBLE:
            plate_html = '<span style="background:rgba(100,116,139,0.2);color:#94a3b8;padding:2px 8px;border-radius:4px;border:1px solid rgba(100,116,139,0.4);font-weight:700;font-family:monospace;font-size:10px;">PLATE NOT VISIBLE</span>'
        else:
            plate_html = f'<span class="plate-tag">{plate_display}</span>'

        sim_badge = '<span style="margin-left:6px;background:rgba(245,158,11,0.2);color:#fbbf24;padding:1px 6px;border-radius:4px;border:1px solid rgba(245,158,11,0.4);font-size:9px;font-weight:700;font-family:monospace;">SIMULATED</span>' if is_sim else ""

        st.markdown(
            f"""
            <div style="padding:14px;border-radius:12px;background:{bg_color};border:1px solid {border_color};margin-bottom:8px;font-family:monospace;font-size:12px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <span style="font-weight:700;color:white;display:flex;align-items:center;gap:6px;">
                        <span class="{dot_cls}" style="width:8px;height:8px;border-radius:50%;"></span>
                        #{idx+1} {det.vehicle_type} {det.model}
                    </span>
                    <span class="{badge_cls}">{status_text}{sim_badge}</span>
                </div>
                <div style="display:flex;flex-direction:column;gap:4px;color:#cbd5e1;font-size:11px;">
                    <div style="display:flex;justify-content:space-between;">
                        <span style="color:#94a3b8;">Plate Number:</span>
                        {plate_html}
                    </div>
                    <div style="display:flex;justify-content:space-between;">
                        <span style="color:#94a3b8;">AI Confidence:</span>
                        <span style="color:#34d399;font-weight:700;">{det.confidence}%</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;">
                        <span style="color:#94a3b8;">Helmet Status:</span>
                        <span style="color:{'#f87171' if det.helmet_status == 'NOT_DETECTED' else '#34d399'};font-weight:700;">
                            {'NOT DETECTED' if det.helmet_status == 'NOT_DETECTED' else 'HELMET OK'}
                        </span>
                    </div>
                    {"<div style='display:flex;justify-content:space-between;padding-top:4px;border-top:1px solid rgba(239,68,68,0.2);'><span style='color:#94a3b8;'>Assessed Penalty:</span><span style='color:#f87171;font-weight:900;font-size:12px;'>" + fine_text + "</span></div>" if is_vio else ""}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if is_vio:
            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"Issue e-Challan", key=f"challan_{det.id}", use_container_width=True):
                    vio_record = next((v for v in st.session_state.violations if v.id == det.id.replace("det-", "VIO-")), None)
                    if not vio_record and api_violations:
                        for v in api_violations:
                            if v.plate_number == det.plate_number or (v.plate_number == PLATE_NOT_VISIBLE and det.plate_number == PLATE_NOT_VISIBLE):
                                vio_record = v
                                break
                    if vio_record:
                        st.session_state.show_echallan = True
                        st.session_state.echallan_record = vio_record
                        st.session_state.active_page = "echallan"
                        st.rerun()
            with c2:
                if st.button("View in Audit", key=f"view_{det.id}", use_container_width=True):
                    vio_record = None
                    if api_violations:
                        for v in api_violations:
                            if v.plate_number == det.plate_number or (v.plate_number == PLATE_NOT_VISIBLE and det.plate_number == PLATE_NOT_VISIBLE):
                                vio_record = v
                                break
                    if vio_record:
                        st.session_state.selected_violation_id = vio_record.id
                        st.session_state.active_page = "violation_detail"
                        st.rerun()

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
    if st.button("Open Violations Management Table", use_container_width=True):
        st.session_state.active_page = "violations"
        st.rerun()


def _render_idle_instructions():
    api_ok = health_check()
    if not api_ok:
        st.markdown(
            """
            <div style="padding:20px;border-radius:16px;background:#090d16;border:1px solid rgba(239,68,68,0.3);font-family:monospace;font-size:12px;">
                <div style="font-weight:700;color:#f87171;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">
                    Backend API Not Running
                </div>
                <p style="color:#94a3b8;margin:0;">
                    Start the FastAPI backend before uploading media:
                </p>
                <code style="display:block;margin-top:8px;padding:8px;background:#0c121e;border-radius:6px;color:#34d399;font-size:11px;">
                    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
                </code>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        """
        <div style="padding:16px;border-radius:16px;background:#090d16;border:1px solid #182338;font-family:monospace;font-size:12px;">
            <div style="font-weight:700;color:white;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:12px;
                        display:flex;align-items:center;gap:8px;">
                <span style="color:#f59e0b;">Traffic Signal AI Verification Rules</span>
            </div>
            <div style="display:flex;flex-direction:column;gap:8px;">
                <div style="padding:10px;border-radius:12px;background:#0c121e;border:1px solid rgba(239,68,68,0.3);
                            display:flex;align-items:flex-start;gap:8px;">
                    <span style="width:8px;height:8px;border-radius:50%;background:#ef4444;margin-top:4px;flex-shrink:0;"></span>
                    <div>
                        <strong style="color:#f87171;font-weight:600;">1. No Helmet Infraction:</strong>
                        <span style="color:#94a3b8;"> Real-time YOLOv8 detection via backend API.</span>
                    </div>
                </div>
                <div style="padding:10px;border-radius:12px;background:#0c121e;border:1px solid rgba(245,158,11,0.3);
                            display:flex;align-items:flex-start;gap:8px;">
                    <span style="width:8px;height:8px;border-radius:50%;background:#f59e0b;margin-top:4px;flex-shrink:0;"></span>
                    <div>
                        <strong style="color:#fbbf24;font-weight:600;">2. Red Light Signal Breach:</strong>
                        <span style="color:#94a3b8;"> Auto-simulated for demo (no stop-line ROI configured).</span>
                    </div>
                </div>
                <div style="padding:10px;border-radius:12px;background:#0c121e;border:1px solid rgba(239,68,68,0.3);
                            display:flex;align-items:flex-start;gap:8px;">
                    <span style="width:8px;height:8px;border-radius:50%;background:#ef4444;margin-top:4px;flex-shrink:0;"></span>
                    <div>
                        <strong style="color:#f87171;font-weight:600;">3. Wrong-Side Contraflow:</strong>
                        <span style="color:#94a3b8;"> Real-time trajectory analysis via backend API.</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
