import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from components.styles import inject_global_css
from lib.mock_data import INITIAL_VIOLATIONS, DEFAULT_DETECTIONS, FINE_AMOUNTS, LAW_SECTIONS

st.set_page_config(
    page_title="RideSafe AI - Two-Wheeler Traffic Safety Intelligence",
    page_icon="\U0001f6a1",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_global_css()

if "violations" not in st.session_state:
    st.session_state.violations = list(INITIAL_VIOLATIONS)
if "active_page" not in st.session_state:
    st.session_state.active_page = "upload"
if "selected_violation_id" not in st.session_state:
    st.session_state.selected_violation_id = None
if "uploaded_media" not in st.session_state:
    st.session_state.uploaded_media = None
if "analysis_running" not in st.session_state:
    st.session_state.analysis_running = False
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "detections" not in st.session_state:
    st.session_state.detections = []
if "show_echallan" not in st.session_state:
    st.session_state.show_echallan = False
if "echallan_record" not in st.session_state:
    st.session_state.echallan_record = None

violations = st.session_state.violations
pending_count = sum(1 for v in violations if v.status == "PENDING_REVIEW")
critical_count = sum(1 for v in violations if v.type in ("RED_LIGHT", "NO_HELMET"))


def render_header():
    active = st.session_state.active_page

    nav_html = '<div style="display:flex;align-items:center;gap:6px;background:#0c121e;padding:4px;border-radius:12px;border:1px solid #1b273d;font-family:monospace;font-size:12px;">'

    pages = [
        ("upload", "AI Vision Lab", "active-green"),
        ("violations", "Violations", "active-red"),
        ("analytics", "Analytics", "active-amber"),
    ]

    for key, label, active_cls in pages:
        if active == key:
            nav_html += f'<span class="nav-tab {active_cls}">{label}</span>'
        else:
            nav_html += f'<span class="nav-tab" style="cursor:pointer;">{label}</span>'

    nav_html += "</div>"

    status_html = f"""
    <div style="display:flex;align-items:center;gap:10px;background:#0c121e;padding:8px 12px;border-radius:12px;border:1px solid #1b273d;font-family:monospace;font-size:11px;">
        <span style="display:flex;align-items:center;gap:4px;color:#f87171;">
            <span class="dot-red"></span>
            <span style="font-weight:700;">{critical_count}</span>
        </span>
        <span style="color:#334155;">|</span>
        <span style="display:flex;align-items:center;gap:4px;color:#fbbf24;">
            <span class="dot-amber"></span>
            <span style="font-weight:700;">{pending_count}</span>
        </span>
        <span style="color:#334155;">|</span>
        <span style="display:flex;align-items:center;gap:4px;color:#34d399;">
            <span class="dot-green pulse-anim"></span>
            <span style="font-weight:600;">Signal ON</span>
        </span>
    </div>
    """

    col1, col2, col3 = st.columns([1.2, 2, 1.2])
    with col1:
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="display:inline-flex;flex-direction:column;align-items:center;justify-content:space-between;background:#0b0f19;border:1px solid #334155;border-radius:6px;padding:4px;gap:3px;box-shadow:0 4px 12px rgba(0,0,0,0.8);width:24px;height:64px;">
                    <div style="width:10px;height:10px;border-radius:50%;background:#ef4444;box-shadow:0 0 8px #ef4444;"></div>
                    <div style="width:10px;height:10px;border-radius:50%;background:#f59e0b;box-shadow:0 0 8px #f59e0b;"></div>
                    <div style="width:10px;height:10px;border-radius:50%;background:#10b981;box-shadow:0 0 8px #10b981;"></div>
                </div>
                <div>
                    <span class="ride-brand">Traffic<span class="ride-brand-red">Light</span> <span class="ride-brand-amber">AI</span></span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(nav_html, unsafe_allow_html=True)
    with col3:
        st.markdown(status_html, unsafe_allow_html=True)


render_header()

st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

page = st.session_state.active_page

if page == "upload":
    from pages import upload_page
    upload_page.render()
elif page == "violations":
    from pages import violations_page
    violations_page.render()
elif page == "analytics":
    from pages import analytics_page
    analytics_page.render()
elif page == "violation_detail":
    from pages import violation_detail_page
    violation_detail_page.render()
elif page == "echallan":
    from pages import echallan_page
    echallan_page.render()
