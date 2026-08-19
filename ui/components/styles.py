import streamlit as st


GLOBAL_CSS = """
<style>
/* ===== BASE ===== */
.stApp {
    background: #07090e !important;
    color: #e2e8f0 !important;
}

/* Streamlit default elements to hide/darken */
#MainMenu, footer, header {visibility: hidden;}
.stDeployButton {display: none;}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0c121e; }
::-webkit-scrollbar-thumb { background: #1e2d45; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #334155; }

/* ===== CARDS ===== */
.ride-card {
    background: #090d16;
    border: 1px solid #1e2a42;
    border-radius: 16px;
    padding: 20px;
    transition: border-color 0.2s;
}
.ride-card:hover {
    border-color: rgba(245, 158, 11, 0.4);
}

.ride-card-green {
    background: #090d16;
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 16px;
    padding: 20px;
}

.ride-card-red {
    background: #090d16;
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 16px;
    padding: 20px;
}

.ride-card-amber {
    background: #090d16;
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 16px;
    padding: 20px;
}

/* ===== HEADER ===== */
.ride-header {
    background: rgba(7, 11, 18, 0.95);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid #182338;
    padding: 10px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: -1rem -1rem 1rem -1rem;
    position: sticky;
    top: 0;
    z-index: 100;
}

.ride-brand {
    font-weight: 900;
    font-size: 1.25rem;
    color: white;
    letter-spacing: -0.02em;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
}
.ride-brand-red { color: #ef4444; }
.ride-brand-amber { color: #f59e0b; }

/* ===== NAV TABS ===== */
.nav-tab {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 700;
    font-family: monospace;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
    color: #94a3b8;
    background: transparent;
}
.nav-tab:hover { color: white; background: #151f33; }
.nav-tab.active-green {
    background: #10b981;
    color: #000;
    box-shadow: 0 0 12px rgba(16,185,129,0.4);
}
.nav-tab.active-red {
    background: #ef4444;
    color: white;
    box-shadow: 0 0 12px rgba(239,68,68,0.4);
}
.nav-tab.active-amber {
    background: #f59e0b;
    color: #000;
    box-shadow: 0 0 12px rgba(245,158,11,0.4);
}

/* ===== BADGES ===== */
.badge-red {
    background: rgba(239,68,68,0.2);
    color: #f87171;
    border: 1px solid rgba(239,68,68,0.4);
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 10px;
    font-weight: 700;
    font-family: monospace;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
.badge-amber {
    background: rgba(245,158,11,0.2);
    color: #fbbf24;
    border: 1px solid rgba(245,158,11,0.4);
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 10px;
    font-weight: 700;
    font-family: monospace;
}
.badge-green {
    background: rgba(16,185,129,0.2);
    color: #34d399;
    border: 1px solid rgba(16,185,129,0.4);
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 10px;
    font-weight: 700;
    font-family: monospace;
}

/* ===== STATUS DOTS ===== */
.dot-red {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ef4444;
    box-shadow: 0 0 6px #ef4444;
}
.dot-amber {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #f59e0b;
    box-shadow: 0 0 6px #f59e0b;
}
.dot-green {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 6px #10b981;
}

/* ===== PLATE TAG ===== */
.plate-tag {
    background: rgba(0,0,0,0.7);
    color: #fcd34d;
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid rgba(245,158,11,0.5);
    font-weight: 900;
    font-family: monospace;
    font-size: 12px;
}

/* ===== EVIDENCE IMAGE ===== */
.evidence-frame {
    border-radius: 12px;
    border: 1px solid #1a253a;
    overflow: hidden;
    background: black;
}

/* ===== KPI STRIP ===== */
.kpi-green {
    background: #0c121e;
    border: 1px solid rgba(16,185,129,0.3);
    border-radius: 12px;
    padding: 10px;
    text-align: center;
}
.kpi-red {
    background: #0c121e;
    border: 1px solid rgba(239,68,68,0.4);
    border-radius: 12px;
    padding: 10px;
    text-align: center;
}
.kpi-amber {
    background: #0c121e;
    border: 1px solid rgba(245,158,11,0.3);
    border-radius: 12px;
    padding: 10px;
    text-align: center;
}

/* ===== VIOLATION CARD ===== */
.vio-card-pending {
    background: #090d16;
    border: 1px solid #1e2a42;
    border-radius: 16px;
    padding: 16px;
    transition: all 0.2s;
}
.vio-card-pending:hover {
    border-color: rgba(245, 158, 11, 0.5);
}

/* ===== TABLE ===== */
.ride-table {
    width: 100%;
    border-collapse: collapse;
    font-family: monospace;
    font-size: 12px;
}
.ride-table th {
    background: #0c121e;
    color: #94a3b8;
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid #182338;
    font-size: 11px;
}
.ride-table td {
    padding: 14px 16px;
    border-bottom: 1px solid #141b2a;
    color: #e2e8f0;
}
.ride-table tr:hover td {
    background: #0c121e;
}

/* ===== BUTTONS ===== */
.btn-green {
    background: #10b981;
    color: #000;
    font-weight: 800;
    border: none;
    padding: 8px 16px;
    border-radius: 10px;
    font-family: monospace;
    font-size: 12px;
    cursor: pointer;
    box-shadow: 0 0 15px rgba(16,185,129,0.35);
    transition: all 0.2s;
}
.btn-green:hover { background: #34d399; }

.btn-red-outline {
    background: rgba(239,68,68,0.15);
    color: #f87171;
    border: 1px solid rgba(239,68,68,0.4);
    padding: 8px 16px;
    border-radius: 10px;
    font-family: monospace;
    font-size: 11px;
    font-weight: 700;
    cursor: pointer;
}

.btn-dark {
    background: #141d31;
    color: #e2e8f0;
    border: 1px solid #223352;
    padding: 8px 16px;
    border-radius: 10px;
    font-family: monospace;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
}
.btn-dark:hover { background: #1a2742; }

/* ===== ANIMATIONS ===== */
@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
.pulse-anim {
    animation: pulse-dot 2s infinite;
}

@keyframes scan-line {
    0% { top: 0; }
    100% { top: 100%; }
}

/* ===== HEATMAP CELL ===== */
.heat-low {
    background: rgba(16,185,129,0.5);
    color: white;
    padding: 6px 8px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 11px;
    text-align: center;
}
.heat-med {
    background: #f59e0b;
    color: #000;
    padding: 6px 8px;
    border-radius: 8px;
    font-weight: 800;
    font-size: 11px;
    text-align: center;
    box-shadow: 0 0 8px rgba(245,158,11,0.4);
}
.heat-high {
    background: #ef4444;
    color: white;
    padding: 6px 8px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 11px;
    text-align: center;
}
.heat-crit {
    background: #ef4444;
    color: white;
    padding: 6px 8px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 11px;
    text-align: center;
    box-shadow: 0 0 12px rgba(239,68,68,0.7);
    outline: 1px solid #fca5a5;
}

/* ===== MINI METRIC ===== */
.mini-metric-label {
    font-size: 10px;
    color: #94a3b8;
    font-weight: 700;
    font-family: monospace;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.mini-metric-value {
    font-size: 1.5rem;
    font-weight: 900;
    color: white;
    font-family: monospace;
}

/* ===== SECTION TITLE ===== */
.section-title {
    font-size: 14px;
    font-weight: 700;
    color: white;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-family: monospace;
    margin-bottom: 8px;
}

/* ===== PROGRESS BAR ===== */
.progress-bar-bg {
    background: #141d31;
    border-radius: 8px;
    height: 6px;
    overflow: hidden;
    width: 100%;
}
.progress-bar-fill {
    height: 100%;
    border-radius: 8px;
    transition: width 0.3s;
}
.progress-green {
    background: #10b981;
    box-shadow: 0 0 8px #10b981;
}
.progress-amber {
    background: #f59e0b;
    box-shadow: 0 0 8px #f59e0b;
}
.progress-red {
    background: #ef4444;
    box-shadow: 0 0 8px #ef4444;
}

/* ===== DOSSIER HUD ===== */
.hud-corners {
    position: relative;
}
.hud-corners::before,
.hud-corners::after {
    content: '';
    position: absolute;
    width: 16px;
    height: 16px;
    border-color: white;
}
.hud-tl { position: absolute; top: -4px; left: -4px; width: 16px; height: 16px; border-top: 2px solid white; border-left: 2px solid white; }
.hud-tr { position: absolute; top: -4px; right: -4px; width: 16px; height: 16px; border-top: 2px solid white; border-right: 2px solid white; }
.hud-bl { position: absolute; bottom: -4px; left: -4px; width: 16px; height: 16px; border-bottom: 2px solid white; border-left: 2px solid white; }
.hud-br { position: absolute; bottom: -4px; right: -4px; width: 16px; height: 16px; border-bottom: 2px solid white; border-right: 2px solid white; }

/* ===== ECHALLAN PRINT ===== */
.echallan-sheet {
    background: white;
    color: #1e293b;
    border-radius: 12px;
    padding: 24px;
    font-family: monospace;
    font-size: 12px;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
}
.echallan-sheet .title {
    font-size: 14px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: -0.02em;
}
.echallan-sheet .subtitle {
    font-size: 10px;
    color: #64748b;
}
.echallan-sheet .fine-amount {
    font-size: 24px;
    font-weight: 900;
    color: #dc2626;
}

/* ===== DIVIDER ===== */
.divider {
    border-bottom: 1px solid #182338;
    margin: 16px 0;
}
</style>
"""


def inject_global_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
