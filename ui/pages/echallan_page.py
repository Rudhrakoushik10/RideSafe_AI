import streamlit as st


def render():
    record = st.session_state.echallan_record
    if not record:
        st.session_state.active_page = "violations"
        st.rerun()
        return

    if st.button("Back to Violations", key="back_from_echallan"):
        st.session_state.active_page = "violations"
        st.rerun()

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="display:flex;justify-content:space-between;align-items:center;padding:16px;
                    background:#0d1424;border-bottom:1px solid #1b263c;border-radius:12px 12px 0 0;">
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="display:inline-flex;flex-direction:column;align-items:center;justify-content:space-between;
                            background:#0b0f19;border:1px solid #334155;border-radius:6px;padding:4px;gap:3px;
                            box-shadow:0 4px 12px rgba(0,0,0,0.8);width:24px;height:64px;">
                    <div style="width:10px;height:10px;border-radius:50%;background:#ef4444;box-shadow:0 0 8px #ef4444;"></div>
                    <div style="width:10px;height:10px;border-radius:50%;background:#f59e0b;box-shadow:0 0 8px #f59e0b;"></div>
                    <div style="width:10px;height:10px;border-radius:50%;background:#10b981;box-shadow:0 0 8px #10b981;"></div>
                </div>
                <div>
                    <h2 style="font-size:14px;font-weight:700;color:white;font-family:monospace;margin:0;">
                        DIGITAL e-CHALLAN ENFORCEMENT RECORD
                    </h2>
                    <p style="font-size:12px;color:#94a3b8;font-family:monospace;margin:2px 0 0 0;">
                        TrafficLight AI - Automated Traffic Signal Enforcement System
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="echallan-sheet">
            <div style="display:flex;justify-content:space-between;border-bottom:2px solid #1e293b;padding-bottom:12px;margin-bottom:16px;">
                <div>
                    <div class="title">TRAFFIC ENFORCEMENT SIGNAL COMMAND</div>
                    <div class="subtitle">Automated Computer-Vision Traffic Violation Notice</div>
                </div>
                <div style="text-align:right;">
                    <div class="subtitle">Challan No:</div>
                    <div style="font-weight:900;font-size:12px;">{record.violation_number}</div>
                </div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:8px 0;border-bottom:1px solid #e2e8f0;font-size:11px;">
                <div>
                    <div style="color:#64748b;">Registration Plate:</div>
                    <div style="font-weight:900;font-size:16px;background:#fde047;padding:2px 8px;border-radius:4px;display:inline-block;margin-top:4px;">
                        {record.plate_number}
                    </div>
                </div>
                <div>
                    <div style="color:#64748b;">Vehicle Classification:</div>
                    <div style="font-weight:700;margin-top:4px;">{record.vehicle_type}</div>
                </div>
                <div>
                    <div style="color:#64748b;">Violation Offense:</div>
                    <div style="font-weight:700;color:#dc2626;margin-top:4px;">{record.type.replace('_', ' ')}</div>
                </div>
                <div>
                    <div style="color:#64748b;">Applicable Motor Vehicles Act:</div>
                    <div style="font-weight:700;margin-top:4px;">{record.law_section}</div>
                </div>
                <div>
                    <div style="color:#64748b;">Traffic Zone / Sector:</div>
                    <div style="font-weight:600;color:#334151;margin-top:4px;">{record.location}</div>
                </div>
                <div>
                    <div style="color:#64748b;">Date & Timestamp:</div>
                    <div style="font-weight:600;color:#334151;margin-top:4px;">{record.timestamp}</div>
                </div>
            </div>

            <div style="margin-top:16px;">
                <div style="font-size:10px;font-weight:700;text-transform:uppercase;color:#64748b;margin-bottom:8px;">
                    Photographic Computer-Vision Evidence
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                    <div style="border-radius:8px;overflow:hidden;border:1px solid #cbd5e1;position:relative;">
                        <img src="{record.evidence.vehicle_crop_url}" style="width:100%;height:140px;object-fit:cover;" />
                        <span style="position:absolute;bottom:4px;left:4px;background:rgba(0,0,0,0.8);color:white;
                                     font-size:8px;padding:2px 6px;border-radius:4px;">
                            Vehicle Crop ({record.confidence}% conf)
                        </span>
                    </div>
                    <div style="border-radius:8px;overflow:hidden;border:1px solid #cbd5e1;position:relative;">
                        <img src="{record.evidence.plate_crop_url}" style="width:100%;height:140px;object-fit:cover;" />
                        <span style="position:absolute;bottom:4px;left:4px;background:rgba(0,0,0,0.8);color:white;
                                     font-size:8px;padding:2px 6px;border-radius:4px;">
                            ANPR Plate Crop ({record.ocr_confidence.overall}%)
                        </span>
                    </div>
                </div>
            </div>

            <div style="display:flex;justify-content:space-between;align-items:center;padding-top:16px;border-top:2px solid #1e293b;margin-top:16px;">
                <div>
                    <div style="font-size:10px;color:#64748b;">Total Penalty Fine Assessed:</div>
                    <div class="fine-amount">Rs.{record.fine_amount:,}</div>
                    <div style="font-size:9px;color:#64748b;margin-top:2px;">
                        Payable within 15 days via Traffic Safety / e-Challan Portal
                    </div>
                </div>
                <div style="display:flex;flex-direction:column;align-items:center;padding:8px;border:1px solid #cbd5e1;
                            border-radius:4px;background:#f8fafc;">
                    <div style="width:56px;height:56px;background:#1e293b;color:white;display:flex;align-items:center;
                                justify-content:center;border-radius:4px;font-size:7px;font-weight:700;text-align:center;
                                border:1px dashed white;">
                        SIGNAL QR PAY
                    </div>
                    <span style="font-size:8px;color:#64748b;margin-top:4px;">Scan to Pay</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    col_info, col_actions = st.columns([2, 1])
    with col_info:
        status_display = record.status.replace("_", " ")
        st.markdown(
            f"""
            <div style="font-family:monospace;font-size:12px;display:flex;align-items:center;gap:8px;">
                <span style="color:#94a3b8;">Status:</span>
                <span style="color:#34d399;font-weight:700;display:flex;align-items:center;gap:4px;">
                    <span class="dot-green pulse-anim" style="width:8px;height:8px;border-radius:50%;"></span>
                    {status_display}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_actions:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Print Notice", use_container_width=True, key="print_challan"):
                st.toast("Print dialog would open here")
        with c2:
            if st.button("Download PDF", use_container_width=True, type="primary", key="download_challan"):
                st.toast("PDF downloaded successfully!")
