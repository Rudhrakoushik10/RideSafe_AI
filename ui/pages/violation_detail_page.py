import streamlit as st
from lib.mock_data import VIOLATION_BADGES, FINE_AMOUNTS
from lib.simulator import PLATE_NOT_VISIBLE

VIOLATION_BADGES_LOCAL = {
    "NO_HELMET": {"label": "NO HELMET", "color": "red"},
    "NO_HELMET_PILLION": {"label": "NO HELMET", "color": "red"},
    "RED_LIGHT": {"label": "RED LIGHT", "color": "red"},
    "WRONG_SIDE": {"label": "WRONG SIDE", "color": "orange"},
}


def _plate_tag(plate_number):
    if plate_number == PLATE_NOT_VISIBLE:
        return (
            '<span style="background:rgba(100,116,139,0.2);color:#94a3b8;padding:2px 8px;border-radius:4px;'
            'border:1px solid rgba(100,116,139,0.4);font-weight:700;font-family:monospace;font-size:12px;">'
            'PLATE NOT VISIBLE</span>'
        )
    return f'<span class="plate-tag" style="font-size:13px;">{plate_number}</span>'


def render():
    vio_id = st.session_state.selected_violation_id
    if not vio_id:
        st.session_state.active_page = "violations"
        st.rerun()
        return

    record = next((v for v in st.session_state.violations if v.id == vio_id), None)
    if not record:
        st.session_state.active_page = "violations"
        st.rerun()
        return

    if st.button("Back to Violations", key="back_from_detail"):
        st.session_state.active_page = "violations"
        st.rerun()

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    is_sim = "SIMULATED" in getattr(record, "notes", "")
    badge = VIOLATION_BADGES_LOCAL.get(record.type, {"label": record.type, "color": "red"})
    badge_cls = f"badge-{badge['color']}" if badge["color"] in ("red", "amber", "green") else "badge-red"

    if is_sim:
        st.markdown(
            '<div style="padding:12px;border-radius:12px;background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.3);'
            'font-family:monospace;font-size:12px;color:#fbbf24;margin-bottom:12px;display:flex;align-items:center;gap:8px;">'
            '<span class="dot-amber"></span> '
            '<strong>SIMULATED VIOLATION</strong> — This red-light violation was programmatically generated for demonstration. '
            'No stop-line ROI is configured for this camera. The violation type and evidence are illustrative only.</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:12px;padding:16px;background:#0d1424;
                    border-bottom:1px solid #1b263c;border-radius:12px 12px 0 0;margin-bottom:16px;">
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:space-between;
                        background:#0b0f19;border:1px solid #334155;border-radius:6px;padding:4px;gap:3px;
                        box-shadow:0 4px 12px rgba(0,0,0,0.8);width:24px;height:64px;">
                <div style="width:10px;height:10px;border-radius:50%;background:#ef4444;box-shadow:0 0 8px #ef4444;"></div>
                <div style="width:10px;height:10px;border-radius:50%;background:#f59e0b;box-shadow:0 0 8px #f59e0b;"></div>
                <div style="width:10px;height:10px;border-radius:50%;background:#10b981;box-shadow:0 0 8px #10b981;"></div>
            </div>
            <div>
                <div style="display:flex;align-items:center;gap:8px;">
                    <h2 style="font-size:14px;font-weight:700;color:white;font-family:monospace;margin:0;">
                        EVIDENCE DOSSIER: {record.violation_number}
                    </h2>
                    <span class="{badge_cls}">{badge['label']}</span>
                    {"<span style='margin-left:4px;background:rgba(245,158,11,0.2);color:#fbbf24;padding:1px 6px;border-radius:4px;border:1px solid rgba(245,158,11,0.4);font-size:9px;font-weight:700;font-family:monospace;'>SIMULATED</span>" if is_sim else ""}
                </div>
                <p style="font-size:12px;color:#94a3b8;font-family:monospace;margin:2px 0 0 0;">
                    Traffic Signal & AI Vision Certified Infraction Record
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([7, 5])

    with left:
        ev_frame = record.evidence.full_frame_url or ""
        ev_vehicle = record.evidence.vehicle_crop_url or ""
        ev_plate = record.evidence.plate_crop_url or ""
        ev_helmet = record.evidence.helmet_crop_url

        has_helmet = bool(ev_helmet)
        tab_labels = ["Vehicle Crop", "Full Frame"]
        if ev_plate:
            tab_labels.insert(1, "Plate ANPR")
        if has_helmet:
            tab_labels.insert(2, "Head/Helmet")

        evidence_tabs = st.tabs(tab_labels)
        tab_idx = 0

        with evidence_tabs[tab_idx]:
            if ev_vehicle:
                st.image(ev_vehicle, use_container_width=True)
            else:
                st.info("No vehicle crop available")
        tab_idx += 1

        if ev_plate:
            with evidence_tabs[tab_idx]:
                st.image(ev_plate, use_container_width=True)
            tab_idx += 1

        if has_helmet:
            with evidence_tabs[tab_idx]:
                st.image(ev_helmet, use_container_width=True)
            tab_idx += 1

        with evidence_tabs[tab_idx]:
            if ev_frame:
                st.image(ev_frame, use_container_width=True)
            else:
                st.info("No full frame available")

        ocr_conf = record.ocr_confidence.overall
        if record.plate_number == PLATE_NOT_VISIBLE or ocr_conf == 0:
            st.markdown(
                """
                <div style="padding:14px;border-radius:12px;background:#0c1220;border:1px solid #1a253a;
                            font-family:monospace;font-size:12px;margin-top:8px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                        <span style="color:#cbd5e1;font-weight:700;display:flex;align-items:center;gap:6px;">
                            ANPR Character-Level OCR Breakdown
                        </span>
                        <span style="color:#94a3b8;font-weight:700;">
                            Plate Not Readable
                        </span>
                    </div>
                    <div style="padding:12px;border-radius:8px;background:rgba(100,116,139,0.1);border:1px solid rgba(100,116,139,0.2);text-align:center;">
                        <div style="font-size:12px;color:#94a3b8;font-family:monospace;">
                            Clear view of number plate not available in this frame.
                        </div>
                        <div style="font-size:10px;color:#64748b;margin-top:4px;">
                            Manual verification or alternative camera angle required.
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="padding:14px;border-radius:12px;background:#0c1220;border:1px solid #1a253a;
                            font-family:monospace;font-size:12px;margin-top:8px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                        <span style="color:#cbd5e1;font-weight:700;display:flex;align-items:center;gap:6px;">
                            ANPR Character-Level OCR Breakdown
                        </span>
                        <span style="color:#34d399;font-weight:700;">
                            Avg OCR: {ocr_conf}%
                        </span>
                    </div>
                    <div style="display:flex;gap:6px;flex-wrap:wrap;">
                """
                + "".join([
                    f"""
                    <div style="padding:6px;border-radius:8px;background:#121a2c;border:1px solid #202d45;
                                text-align:center;min-width:34px;">
                        <div style="font-size:12px;font-family:monospace;font-weight:900;color:#fcd34d;">{c.char}</div>
                        <div style="font-size:8px;font-family:monospace;color:#34d399;margin-top:2px;">{c.confidence}%</div>
                    </div>
                    """
                    for c in record.ocr_confidence.characters
                ])
                + """
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with right:
        status_display = record.status.replace("_", " ")
        plate_html = _plate_tag(record.plate_number)
        st.markdown(
            f"""
            <div style="padding:16px;border-radius:12px;background:#0c1220;border:1px solid #1a253a;
                        font-family:monospace;font-size:12px;">
                <div style="font-size:11px;text-transform:uppercase;color:#94a3b8;font-weight:700;
                            border-bottom:1px solid #182338;padding-bottom:8px;margin-bottom:12px;
                            display:flex;justify-content:space-between;">
                    <span>Violation Telemetry</span>
                    <span style="color:#f87171;font-weight:700;">{status_display}</span>
                </div>
                <div style="display:flex;flex-direction:column;gap:10px;">
                    <div style="display:flex;justify-content:space-between;">
                        <span style="color:#94a3b8;">Violation Type:</span>
                        <span style="color:white;font-weight:700;">{record.type.replace('_', ' ')}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="color:#94a3b8;">License Plate:</span>
                        {plate_html}
                    </div>
                    <div style="display:flex;justify-content:space-between;">
                        <span style="color:#94a3b8;">Vehicle Type:</span>
                        <span style="color:#cbd5e1;">{record.vehicle_type}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;">
                        <span style="color:#94a3b8;">Detection Confidence:</span>
                        <span style="color:#34d399;font-weight:700;">{record.confidence}%</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;">
                        <span style="color:#94a3b8;">Speed / Limit:</span>
                        <span style="color:#cbd5e1;">{record.speed_kmh} km/h (Limit: {record.speed_limit})</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;">
                        <span style="color:#94a3b8;">Traffic Zone:</span>
                        <span style="color:#cbd5e1;text-align:right;max-width:180px;overflow:hidden;text-overflow:ellipsis;">
                            {record.location}
                        </span>
                    </div>
                    <div style="display:flex;justify-content:space-between;">
                        <span style="color:#94a3b8;">Timestamp:</span>
                        <span style="color:#cbd5e1;">{record.timestamp}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding-top:8px;border-top:1px solid #182338;">
                        <span style="color:#94a3b8;font-weight:700;">Assessed Penalty:</span>
                        <span style="font-size:1.25rem;font-weight:900;color:#34d399;">
                            Rs.{record.fine_amount:,}
                        </span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        law_color = "#fbbf24" if is_sim else "#cbd5e1"
        st.markdown(
            f"""
            <div style="padding:12px;border-radius:12px;background:#0e1628;border:1px solid #1e2d4a;
                        font-family:monospace;font-size:12px;margin-top:12px;">
                <div style="font-size:10px;color:#94a3b8;font-weight:700;text-transform:uppercase;">Applicable Law</div>
                <div style="color:{law_color};font-weight:600;">{record.law_section}</div>
                <p style="font-size:10px;color:#94a3b8;margin-top:4px;">{record.notes}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        reviewer_notes = st.text_area(
            "Operator Remarks (Optional)",
            placeholder="Add manual verification remarks or justification notes...",
            key="reviewer_notes",
            height=80,
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("e-Challan PDF", use_container_width=True, key="detail_echallan"):
                st.session_state.show_echallan = True
                st.session_state.echallan_record = record
                st.session_state.active_page = "echallan"
                st.rerun()
        with c2:
            if st.button("Issue Challan", use_container_width=True, type="primary", key="detail_issue"):
                record.status = "CHALLAN_ISSUED"
                if reviewer_notes:
                    record.notes = reviewer_notes
                st.session_state.show_echallan = True
                st.session_state.echallan_record = record
                st.session_state.active_page = "echallan"
                st.rerun()

        c3, c4 = st.columns(2)
        with c3:
            if st.button("Mark Reviewed", use_container_width=True, key="detail_review"):
                record.status = "VERIFIED"
                if reviewer_notes:
                    record.notes = reviewer_notes
                st.session_state.active_page = "violations"
                st.rerun()
        with c4:
            if st.button("Dismiss", use_container_width=True, key="detail_dismiss"):
                record.status = "DISMISSED"
                if reviewer_notes:
                    record.notes = reviewer_notes
                st.session_state.active_page = "violations"
                st.rerun()
