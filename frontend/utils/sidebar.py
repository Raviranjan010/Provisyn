"""PROVISYN Persistent Sidebar Navigation.
Strict 14-item Information Architecture (Part 11 IA).
"""
import streamlit as st
from backend.core.config import settings

PAGES = [
    {"num": "01", "name": "Command Overview", "path": "streamlit_app.py", "icon": "📊"},
    {"num": "02", "name": "Risk Intelligence", "path": "pages/2_Risk_Intelligence.py", "icon": "⚠️"},
    {"num": "03", "name": "Network Intelligence", "path": "pages/3_Network_Intelligence.py", "icon": "🕸️"},
    {"num": "04", "name": "Hidden Dependencies", "path": "pages/4_Hidden_Dependencies.py", "icon": "🔍"},
    {"num": "05", "name": "Supplier Intelligence", "path": "pages/5_Supplier_Intelligence.py", "icon": "🏢"},
    {"num": "06", "name": "Financial Exposure", "path": "pages/6_Financial_Exposure.py", "icon": "💲"},
    {"num": "07", "name": "Demand & Inventory", "path": "pages/7_Demand_and_Inventory.py", "icon": "📦"},
    {"num": "08", "name": "Resilience Lab", "path": "pages/8_Resilience_Lab.py", "icon": "🧪"},
    {"num": "09", "name": "Recommendations", "path": "pages/9_Recommendations.py", "icon": "🎯"},
    {"num": "10", "name": "PROVISYN Copilot", "path": "pages/10_PROVISYN_Copilot.py", "icon": "🤖"},
    {"num": "11", "name": "Model Intelligence", "path": "pages/11_Model_Intelligence.py", "icon": "📈"},
    {"num": "12", "name": "Alerts & Events", "path": "pages/12_Alerts_and_Events.py", "icon": "🔔"},
    {"num": "13", "name": "Reports", "path": "pages/13_Reports.py", "icon": "📄"},
    {"num": "14", "name": "About", "path": "pages/14_About.py", "icon": "ℹ️"},
]

def render_sidebar(current_page: str = "Command Overview"):
    """Render persistent left navigation with industrial terminal styling."""
    with st.sidebar:
        st.markdown(f"""
        <div style="padding-bottom: 0.75rem; border-bottom: 1px solid #3A3A3C; margin-bottom: 1rem;">
            <div style="font-size: 1.35rem; font-weight: 800; letter-spacing: 0.05em; color: #F5F4F0;">PROVISYN</div>
            <div style="font-size: 0.75rem; color: #9C9A96; margin-top: 2px;">Supply Chain Risk, Resilience & Decision Intelligence</div>
            <div style="font-size: 0.7rem; color: #5B7A63; margin-top: 4px; font-weight: 600;">{settings.AUTHOR}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="sub-label" style="margin-bottom: 0.5rem;">Navigation</div>', unsafe_allow_html=True)
        
        for p in PAGES:
            is_active = (p["name"] == current_page)
            active_style = "background-color: #2B2B2E; border-left: 3px solid #5B7A63;" if is_active else ""
            label = f"{p['num']} {p['name']}"
            try:
                st.page_link(p["path"], label=label, icon=p["icon"], disabled=is_active)
            except Exception:
                # Fallback if running directly without multipage root context
                st.markdown(f'<div style="padding: 4px 8px; font-size: 0.85rem; {active_style}">{p["icon"]} {label}</div>', unsafe_allow_html=True)
        
        st.markdown("""---""")
        st.markdown(f"""
        <div style="font-size: 0.7rem; color: #9C9A96;">
            <div><strong>Engine:</strong> {settings.GRAPH_BACKEND.upper()}</div>
            <div><strong>Backend:</strong> {settings.DATA_BACKEND.upper()}</div>
            <div style="margin-top: 4px; font-size: 0.65rem; line-height: 1.2;">
                Derivative of Snowflake quickstart (Apache-2.0, Copyright Snowflake Inc.)
            </div>
        </div>
        """, unsafe_allow_html=True)
