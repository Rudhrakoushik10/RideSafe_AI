import streamlit as st
import plotly.graph_objects as go
from lib.mock_data import HOURLY_DATA, HEATMAP_HOURS, HEATMAP_DATA


def render():
    st.markdown(
        """
        <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #182338;padding-bottom:12px;">
            <div>
                <h1 style="font-size:1.5rem;font-weight:900;color:white;letter-spacing:-0.02em;font-family:monospace;margin:0;">
                    Traffic Safety & Signal Analytics
                </h1>
                <p style="font-size:12px;color:#94a3b8;margin:4px 0 0 0;font-family:monospace;">
                    Traffic signal compliance rates, hourly risk density, and sector hazard heatmaps.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    time_range = st.selectbox(
        "Time Range",
        ["24h", "7d", "30d"],
        index=0,
        label_visibility="collapsed",
        key="analytics_time_range",
    )

    _render_kpi_cards()
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
    _render_hourly_chart()
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
    _render_heatmap()


def _render_kpi_cards():
    st.markdown(
        """
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;font-family:monospace;font-size:12px;">
            <!-- GREEN: Helmet Compliance -->
            <div class="ride-card-green">
                <div style="display:flex;justify-content:space-between;align-items:center;color:#94a3b8;margin-bottom:8px;">
                    <span style="display:flex;align-items:center;gap:6px;color:#34d399;font-weight:700;">
                        <span class="dot-green"></span>
                        Safe Compliance Rate
                    </span>
                </div>
                <div style="font-size:1.75rem;font-weight:900;color:white;font-family:monospace;">84.6%</div>
                <div style="font-size:11px;color:#34d399;margin-top:4px;">+3.8% increase in protective gear compliance</div>
                <div style="margin-top:12px;">
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill progress-green" style="width:84.6%;"></div>
                    </div>
                </div>
            </div>

            <!-- RED: Peak Infraction Window -->
            <div class="ride-card-red">
                <div style="display:flex;justify-content:space-between;align-items:center;color:#94a3b8;margin-bottom:8px;">
                    <span style="display:flex;align-items:center;gap:6px;color:#f87171;font-weight:700;">
                        <span class="dot-red"></span>
                        Peak Signal Infractions
                    </span>
                </div>
                <div style="font-size:1.75rem;font-weight:900;color:white;font-family:monospace;">18:00 - 19:30</div>
                <div style="font-size:11px;color:#f87171;margin-top:4px;">Evening rush hour accounts for 42% of breaches</div>
                <div style="margin-top:12px;">
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill progress-red" style="width:68%;"></div>
                    </div>
                </div>
            </div>

            <!-- AMBER: AI Detection Precision -->
            <div class="ride-card-amber">
                <div style="display:flex;justify-content:space-between;align-items:center;color:#94a3b8;margin-bottom:8px;">
                    <span style="display:flex;align-items:center;gap:6px;color:#fbbf24;font-weight:700;">
                        <span class="dot-amber"></span>
                        AI ANPR Accuracy
                    </span>
                </div>
                <div style="font-size:1.75rem;font-weight:900;color:#fcd34d;font-family:monospace;">98.4%</div>
                <div style="font-size:11px;color:#94a3b8;margin-top:4px;">Validated across high-density city traffic feeds</div>
                <div style="margin-top:12px;">
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill progress-amber" style="width:98.4%;"></div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_hourly_chart():
    st.markdown(
        """
        <div class="ride-card" style="padding:24px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <div>
                    <div style="font-size:14px;font-weight:700;color:white;text-transform:uppercase;letter-spacing:0.05em;font-family:monospace;">
                        24-Hour Violation Density Timeline
                    </div>
                    <div style="font-size:12px;color:#94a3b8;font-family:monospace;margin-top:4px;">
                        Hourly breakdown by No-Helmet (Red), Red-Light Signal Breaches (Amber), and Contraflow (Yellow)
                    </div>
                </div>
                <div style="display:flex;gap:16px;font-family:monospace;font-size:12px;">
                    <span style="display:flex;align-items:center;gap:6px;color:#cbd5e1;">
                        <span style="width:10px;height:10px;border-radius:50%;background:#ef4444;display:inline-block;"></span>
                        No Helmet
                    </span>
                    <span style="display:flex;align-items:center;gap:6px;color:#cbd5e1;">
                        <span style="width:10px;height:10px;border-radius:50%;background:#f59e0b;display:inline-block;"></span>
                        Red Light
                    </span>
                    <span style="display:flex;align-items:center;gap:6px;color:#cbd5e1;">
                        <span style="width:10px;height:10px;border-radius:50%;background:#ca8a04;display:inline-block;"></span>
                        Wrong Side
                    </span>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    hours = [d["hour"] for d in HOURLY_DATA]
    no_helmet = [d["no_helmet"] for d in HOURLY_DATA]
    red_light = [d["red_light"] for d in HOURLY_DATA]
    wrong_side = [d["wrong_side"] for d in HOURLY_DATA]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="No Helmet",
        x=hours,
        y=no_helmet,
        marker_color="#ef4444",
        hovertemplate="No Helmet: %{y}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Red Light",
        x=hours,
        y=red_light,
        marker_color="#f59e0b",
        hovertemplate="Red Light: %{y}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Wrong Side",
        x=hours,
        y=wrong_side,
        marker_color="#ca8a04",
        hovertemplate="Wrong Side: %{y}<extra></extra>",
    ))

    fig.update_layout(
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="monospace", color="#94a3b8", size=11),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        height=320,
        xaxis=dict(
            gridcolor="rgba(24,35,56,0.5)",
            linecolor="#182338",
        ),
        yaxis=dict(
            gridcolor="rgba(24,35,56,0.5)",
            linecolor="#182338",
        ),
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_heatmap():
    st.markdown(
        """
        <div class="ride-card" style="padding:24px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <div>
                    <div style="font-size:14px;font-weight:700;color:white;text-transform:uppercase;letter-spacing:0.05em;
                                font-family:monospace;display:flex;align-items:center;gap:8px;">
                        Traffic Sector Hazard Density Heatmap
                    </div>
                    <div style="font-size:12px;color:#94a3b8;font-family:monospace;margin-top:4px;">
                        Signal hazard density calibrated by traffic light states (Green: Low - Amber: Medium - Red: Critical)
                    </div>
                </div>
                <div style="display:flex;gap:8px;align-items:center;font-family:monospace;font-size:10px;color:#94a3b8;">
                    <span>Low (Green)</span>
                    <span style="width:12px;height:12px;border-radius:3px;background:rgba(16,185,129,0.5);display:inline-block;"></span>
                    <span style="width:12px;height:12px;border-radius:3px;background:#f59e0b;display:inline-block;"></span>
                    <span style="width:12px;height:12px;border-radius:3px;background:#ef4444;display:inline-block;"></span>
                    <span>High (Red Alert)</span>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    sectors = list(HEATMAP_DATA.keys())
    heatmap_z = [HEATMAP_DATA[s] for s in sectors]

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_z,
        x=HEATMAP_HOURS,
        y=sectors,
        colorscale=[
            [0, "rgba(16,185,129,0.3)"],
            [0.3, "rgba(16,185,129,0.5)"],
            [0.5, "#f59e0b"],
            [0.75, "#ef4444"],
            [1, "#dc2626"],
        ],
        text=heatmap_z,
        texttemplate="%{text}",
        textfont=dict(size=12, family="monospace", color="white"),
        hovertemplate="Sector: %{y}<br>Time: %{x}<br>Violations: %{z}<extra></extra>",
        showscale=False,
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="monospace", color="#94a3b8", size=11),
        margin=dict(l=0, r=0, t=0, b=0),
        height=280,
        xaxis=dict(
            side="top",
            gridcolor="rgba(24,35,56,0.3)",
            linecolor="#182338",
        ),
        yaxis=dict(
            autorange="reversed",
            gridcolor="rgba(24,35,56,0.3)",
            linecolor="#182338",
        ),
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
