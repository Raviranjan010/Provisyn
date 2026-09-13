"""PROVISYN — Supply Chain Risk, Resilience & Decision Intelligence.
Command Overview (Page 1) — Executive & Operational Cockpit.
"""
import sys
from pathlib import Path
import streamlit as st

# Setup path resolution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components.styles import inject_provisyn_styles
from frontend.components import render_kpi, render_alert_item, render_risk_badge
from frontend.utils.sidebar import render_sidebar
from backend.core.config import settings
from backend.data.repository import get_repository

st.set_page_config(
    page_title=f"{settings.APP_NAME} — Command Overview",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_provisyn_styles(st)
render_sidebar(current_page="Command Overview")

# Header Strip
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 1.5rem; border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem;">
    <div>
        <h1 style="margin: 0; font-size: 1.75rem;">01 COMMAND OVERVIEW</h1>
        <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">Real-time supply chain operational risk cockpit and posture</div>
    </div>
    <div style="text-align: right;">
        <span class="data-label">MODE: {settings.DATA_BACKEND.upper()}</span>
        <span class="data-label">GRAPH: {settings.GRAPH_BACKEND.upper()}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# KPI Strip
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    render_kpi("Portfolio Resilience", "76.4 / 100", subtext="▲ +2.1 pts vs prior week", data_label="calculated")
with kpi2:
    render_kpi("Revenue at Risk", "$4.82M", subtext="Across 14 open orders", delta="▲ $320K", data_label="simulated")
with kpi3:
    render_kpi("Critical Entities", "4 Nodes", subtext="3 Suppliers, 1 Material", data_label="calculated")
with kpi4:
    render_kpi("SPOF Bottlenecks", "2 Critical", subtext="Outback Lithium, Katanga", data_label="calculated")
with kpi5:
    render_kpi("Stockout Alerts", "3 Skus", subtext="Days of cover < 14d", data_label="observed")

st.markdown("""<div style="margin-top: 1rem;"></div>""", unsafe_allow_html=True)

# Operational Overview Grid
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("### Operational Risk Posture")
    st.markdown("""
    <div class="terminal-card">
        <div style="font-size: 0.85rem; color: #9C9A96; margin-bottom: 0.75rem;">
            SYSTEM POSTURE: High geopolitical and raw material concentration in battery materials.
        </div>
        <p style="font-size: 0.9rem; line-height: 1.5;">
            PROVISYN multi-tier analysis indicates an unhedged reliance on Tier-2 upstream lithium and cobalt extractors.
            Simulations project potential production halts at Module Assembly if primary maritime trade lanes experience >7 days of port delay.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    st.markdown("### Priority Alerts")
    render_alert_item(
        severity="CRITICAL",
        title="Tier-2 Hidden Dependency Discovered",
        message="70% of battery pack manufacturing routes through Outback Lithium Resources via indirect trade flows.",
        entity_id="V10001 / AUS",
        timestamp="10 mins ago"
    )
    render_alert_item(
        severity="WARNING",
        title="Days of Cover Below Safety Threshold",
        message="Electrolyte LiPF6 Solution inventory is at 18 days (safety minimum: 25 days).",
        entity_id="M-3012",
        timestamp="42 mins ago"
    )
