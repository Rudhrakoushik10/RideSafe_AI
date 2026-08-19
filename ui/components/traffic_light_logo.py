import streamlit as st


def render_traffic_light_logo(size: str = "md", active_light: str = "all"):
    sizes = {
        "sm": {"dot": 8, "gap": 2, "pad": 3, "w": 20, "h": 52},
        "md": {"dot": 10, "gap": 3, "pad": 4, "w": 24, "h": 64},
        "lg": {"dot": 14, "gap": 4, "pad": 6, "w": 32, "h": 88},
    }
    s = sizes.get(size, sizes["md"])

    colors = {
        "red": ("#ef4444", "#ef4444") if active_light in ("all", "red") else ("#450a0a", "#7f1d1d"),
        "amber": ("#f59e0b", "#f59e0b") if active_light in ("all", "amber") else ("#78350f", "#92400e"),
        "green": ("#10b981", "#10b981") if active_light in ("all", "green") else ("#064e3b", "#065f46"),
    }

    glow = {
        "red": "0 0 8px #ef4444" if active_light in ("all", "red") else "none",
        "amber": "0 0 8px #f59e0b" if active_light in ("all", "amber") else "none",
        "green": "0 0 8px #10b981" if active_light in ("all", "green") else "none",
    }

    html = f"""
    <div style="display:inline-flex;flex-direction:column;align-items:center;
                justify-content:space-between;background:#0b0f19;
                border:1px solid #334155;border-radius:6px;
                padding:{s['pad']}px;gap:{s['gap']}px;
                box-shadow:0 4px 12px rgba(0,0,0,0.8);
                width:{s['w']}px;height:{s['h']}px;">
        <div style="width:{s['dot']}px;height:{s['dot']}px;border-radius:50%;
                    background:{colors['red'][0]};box-shadow:{glow['red']};
                    border:1px solid {colors['red'][1]};"></div>
        <div style="width:{s['dot']}px;height:{s['dot']}px;border-radius:50%;
                    background:{colors['amber'][0]};box-shadow:{glow['amber']};
                    border:1px solid {colors['amber'][1]};"></div>
        <div style="width:{s['dot']}px;height:{s['dot']}px;border-radius:50%;
                    background:{colors['green'][0]};box-shadow:{glow['green']};
                    border:1px solid {colors['green'][1]};"></div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_traffic_light_inline(size: str = "sm"):
    render_traffic_light_logo(size=size, active_light="all")
