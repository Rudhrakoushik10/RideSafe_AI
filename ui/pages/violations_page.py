import streamlit as st
from lib.mock_data import VIOLATION_BADGES
from lib.simulator import PLATE_NOT_VISIBLE

VIOLATION_BADGES_LOCAL = {
    "NO_HELMET": {"label": "NO HELMET", "color": "red", "icon": "hard_hat"},
    "NO_HELMET_PILLION": {"label": "NO HELMET", "color": "red", "icon": "hard_hat"},
    "RED_LIGHT": {"label": "RED LIGHT", "color": "red", "icon": "alert_octagon"},
    "WRONG_SIDE": {"label": "WRONG SIDE", "color": "orange", "icon": "compass"},
}


def render():
    violations = st.session_state.violations

    st.markdown(
        """
        <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #182338;padding-bottom:12px;">
            <div>
                <h1 style="font-size:1.5rem;font-weight:900;color:white;letter-spacing:-0.02em;font-family:monospace;margin:0;">
                    Traffic Violations Management
                </h1>
                <p style="font-size:12px;color:#94a3b8;margin:4px 0 0 0;font-family:monospace;">
                    Traffic signal infraction verification, officer adjudication, and digital e-Challan penalty enforcement.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    pending = [v for v in violations if v.status == "PENDING_REVIEW"]
    active_fines = [v for v in violations if v.status in ("CHALLAN_ISSUED", "APPROVED", "VERIFIED", "PAID")]

    tab1, tab2 = st.tabs([
        f"Pending Manual Audit ({len(pending)})",
        f"Active Fines ({len(active_fines)})",
    ])

    with tab1:
        _render_pending_tab(pending)

    with tab2:
        _render_active_fines_tab(active_fines)


def _plate_html(record):
    if record.plate_number == PLATE_NOT_VISIBLE:
        return (
            '<span style="background:rgba(100,116,139,0.2);color:#94a3b8;padding:2px 8px;border-radius:4px;'
            'border:1px solid rgba(100,116,139,0.4);font-weight:700;font-family:monospace;font-size:10px;">'
            'PLATE NOT VISIBLE</span>'
        )
    return f'<span class="plate-tag">{record.plate_number}</span>'


def _sim_badge(record):
    if "SIMULATED" in getattr(record, "notes", ""):
        return (
            '<span style="margin-left:6px;background:rgba(245,158,11,0.2);color:#fbbf24;padding:1px 6px;'
            'border-radius:4px;border:1px solid rgba(245,158,11,0.4);font-size:9px;font-weight:700;'
            'font-family:monospace;">SIMULATED</span>'
        )
    return ""


def _render_pending_tab(pending_violations):
    col_search, col_filter, col_conf = st.columns([2, 2, 2])
    with col_search:
        search = st.text_input(
            "Search",
            placeholder="Search license plate, ID, or zone...",
            label_visibility="collapsed",
            key="pending_search",
        )
    with col_filter:
        filter_type = st.selectbox(
            "Filter",
            ["ALL", "NO_HELMET", "RED_LIGHT", "WRONG_SIDE"],
            label_visibility="collapsed",
            key="pending_filter",
            format_func=lambda x: "All Types" if x == "ALL" else x.replace("_", " "),
        )
    with col_conf:
        min_conf = st.slider(
            "Min Confidence",
            min_value=50,
            max_value=100,
            value=50,
            step=1,
            key="pending_conf_threshold",
            help="Show only violations above this confidence",
        )

    filtered = pending_violations
    if search:
        q = search.lower()
        filtered = [v for v in filtered if q in (v.plate_number or "").lower() or q in v.violation_number.lower() or q in v.location.lower()]
    if filter_type != "ALL":
        if filter_type == "NO_HELMET":
            filtered = [v for v in filtered if v.type in ("NO_HELMET", "NO_HELMET_PILLION")]
        else:
            filtered = [v for v in filtered if v.type == filter_type]
    filtered = [v for v in filtered if v.confidence >= min_conf]

    if not filtered:
        st.markdown(
            """
            <div style="padding:48px;text-align:center;border-radius:16px;background:#090d16;border:1px solid #182338;">
                <div style="font-size:2rem;margin-bottom:8px;">&#10003;</div>
                <div style="font-size:14px;font-weight:700;color:white;font-family:monospace;">No Pending Violations (All Clear)</div>
                <p style="font-size:12px;color:#94a3b8;font-family:monospace;margin-top:4px;">
                    All AI-detected events have been audited and verified by traffic officers.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        cols = st.columns(2)
        for idx, record in enumerate(filtered):
            with cols[idx % 2]:
                badge = VIOLATION_BADGES_LOCAL.get(record.type, {"label": record.type, "color": "red"})
                badge_cls = f"badge-{badge['color']}" if badge["color"] in ("red", "amber", "green") else "badge-red"
                sim = _sim_badge(record)
                plate_h = _plate_html(record)

                ev_frame = record.evidence.full_frame_url or ""
                ev_plate = record.evidence.plate_crop_url or ""

                st.markdown(
                    f"""
                    <div class="vio-card-pending" style="margin-bottom:12px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                            <div style="display:flex;align-items:center;gap:8px;">
                                <span class="{badge_cls}">{badge['label']}</span>{sim}
                                <span style="font-size:10px;color:#94a3b8;">{record.time_ago}</span>
                            </div>
                            <span style="font-size:10px;color:#fbbf24;background:rgba(245,158,11,0.15);padding:2px 8px;
                                         border-radius:6px;border:1px solid rgba(245,158,11,0.3);font-weight:700;font-family:monospace;">
                                Pending Officer Audit
                            </span>
                        </div>
                        <div style="display:grid;grid-template-columns:2fr 1fr;gap:8px;margin-bottom:10px;">
                            <div style="position:relative;border-radius:8px;overflow:hidden;background:#0c121e;border:1px solid #1a253a;aspect-ratio:16/9;display:flex;align-items:center;justify-content:center;">
                                {"<img src='" + ev_frame + "' style='width:100%;height:100%;object-fit:cover;' />" if ev_frame else '<span style="color:#94a3b8;font-size:10px;font-family:monospace;">No frame available</span>'}
                                <span style="position:absolute;bottom:4px;left:4px;background:rgba(0,0,0,0.85);color:white;
                                             font-size:8px;padding:2px 6px;border-radius:4px;font-weight:700;">EVIDENCE FRAME</span>
                            </div>
                            <div style="position:relative;border-radius:8px;overflow:hidden;background:#0c121e;border:1px solid #1a253a;aspect-ratio:16/9;display:flex;align-items:center;justify-content:center;">
                                {"<img src='" + ev_plate + "' style='width:100%;height:100%;object-fit:cover;' />" if ev_plate else '<span style="color:#94a3b8;font-size:10px;font-family:monospace;">No plate crop</span>'}
                                <span style="position:absolute;bottom:4px;left:4px;background:rgba(0,0,0,0.85);color:#fcd34d;
                                             font-size:8px;padding:2px 6px;border-radius:4px;font-weight:700;">ANPR CROP</span>
                            </div>
                        </div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:10px;border-radius:12px;
                                    background:#0c121e;border:1px solid #182338;font-size:11px;font-family:monospace;color:#cbd5e1;">
                            <div>
                                <div style="color:#94a3b8;font-size:9px;">LICENSE PLATE</div>
                                <div>{plate_h}</div>
                            </div>
                            <div>
                                <div style="color:#94a3b8;font-size:9px;">AI CONFIDENCE</div>
                                <div style="color:#34d399;font-weight:700;">{record.confidence}%</div>
                            </div>
                            <div>
                                <div style="color:#94a3b8;font-size:9px;">TRAFFIC ZONE</div>
                                <div style="color:white;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{record.location}</div>
                            </div>
                            <div>
                                <div style="color:#94a3b8;font-size:9px;">PROPOSED PENALTY</div>
                                <div style="color:#f87171;font-weight:700;">Rs.{record.fine_amount:,}</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    if st.button("Approve & Issue Fine", key=f"approve_{record.id}", use_container_width=True, type="primary"):
                        record.status = "APPROVED"
                        st.session_state.show_echallan = True
                        st.session_state.echallan_record = record
                        st.session_state.active_page = "echallan"
                        st.rerun()
                with c2:
                    if st.button("Dismiss", key=f"dismiss_{record.id}", use_container_width=True):
                        record.status = "DISMISSED"
                        record.notes = "Dismissed during manual officer audit"
                        st.rerun()
                with c3:
                    if st.button("Inspect", key=f"inspect_{record.id}", use_container_width=True):
                        st.session_state.selected_violation_id = record.id
                        st.session_state.active_page = "violation_detail"
                        st.rerun()


def _render_active_fines_tab(active_fines):
    col_search, col_conf = st.columns([3, 2])
    with col_search:
        search = st.text_input(
            "Search",
            placeholder="Search license plate, ID, or zone...",
            label_visibility="collapsed",
            key="fines_search",
        )
    with col_conf:
        min_conf = st.slider(
            "Min Confidence",
            min_value=50,
            max_value=100,
            value=50,
            step=1,
            key="fines_conf_threshold",
            help="Show only fines above this confidence",
        )

    filtered = active_fines
    if search:
        q = search.lower()
        filtered = [v for v in filtered if q in (v.plate_number or "").lower() or q in v.violation_number.lower() or q in v.location.lower()]
    filtered = [v for v in filtered if v.confidence >= min_conf]

    if not filtered:
        st.markdown(
            """
            <div style="padding:48px;text-align:center;border-radius:16px;background:#090d16;border:1px solid #182338;">
                <div style="font-size:2rem;margin-bottom:8px;">&#128196;</div>
                <div style="font-size:14px;font-weight:700;color:white;font-family:monospace;">No Active Fines Recorded</div>
                <p style="font-size:12px;color:#94a3b8;font-family:monospace;margin-top:4px;">
                    Approved violations will appear here with e-Challan references and penalty status.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        table_html = """
        <div style="overflow-x:auto;border-radius:16px;background:#090d16;border:1px solid #182338;">
            <table class="ride-table">
                <thead>
                    <tr>
                        <th>Challan Ref #</th>
                        <th>Offense</th>
                        <th>Vehicle Plate</th>
                        <th>Traffic Zone</th>
                        <th>Assessed Fine</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
        """

        for record in filtered:
            badge = VIOLATION_BADGES_LOCAL.get(record.type, {"label": record.type, "color": "red"})
            is_paid = record.status == "PAID"
            status_badge = '<span class="badge-green">PAID</span>' if is_paid else '<span class="badge-red">UNPAID</span>'
            plate_h = _plate_html(record)
            sim = _sim_badge(record)

            table_html += f"""
                    <tr>
                        <td style="font-weight:700;color:white;white-space:nowrap;">
                            <span class="dot-red" style="margin-right:6px;"></span>
                            {record.violation_number}
                        </td>
                        <td><span class="badge-red">{badge['label']}</span>{sim}</td>
                        <td>{plate_h}</td>
                        <td style="color:#cbd5e1;white-space:nowrap;">{record.location}</td>
                        <td style="font-weight:700;color:#f87171;white-space:nowrap;">Rs.{record.fine_amount:,}</td>
                        <td>{status_badge}</td>
                    </tr>
            """

        table_html += "</tbody></table></div>"
        st.markdown(table_html, unsafe_allow_html=True)

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        for record in filtered:
            c1, c2 = st.columns([4, 1])
            with c2:
                if st.button("e-Challan", key=f"echallan_{record.id}", use_container_width=True):
                    st.session_state.show_echallan = True
                    st.session_state.echallan_record = record
                    st.session_state.active_page = "echallan"
                    st.rerun()
                if st.button("View", key=f"view_detail_{record.id}", use_container_width=True):
                    st.session_state.selected_violation_id = record.id
                    st.session_state.active_page = "violation_detail"
                    st.rerun()
