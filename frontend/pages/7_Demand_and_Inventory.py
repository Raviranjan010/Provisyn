"""PROVISYN — Demand & Inventory (Page 7).
Risk-aware safety stock optimization, days of cover, reorder point triggers, and stockout probability prediction.
"""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components.styles import (
    inject_provisyn_styles,
    COLOR_SURFACE,
    COLOR_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_RISK_HEALTHY,
    COLOR_RISK_WARNING,
    COLOR_RISK_CRITICAL,
)
from frontend.components import render_kpi, render_risk_badge
from frontend.utils.sidebar import render_sidebar
from backend.data.repository import get_repository
from backend.data.generator import seed_database
from backend.engines.inventory import InventoryEngine

st.set_page_config(page_title="PROVISYN — Demand & Inventory", layout="wide")
inject_provisyn_styles(st)
render_sidebar(current_page="Demand & Inventory")

st.markdown("""
<div style="border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: baseline;">
    <div>
        <h1 style="margin: 0; font-size: 1.75rem;">07 DEMAND & INVENTORY INTELLIGENCE</h1>
        <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">Dynamic risk-aware safety stock calculation, days of cover analytics, and predictive stockout forecasting</div>
    </div>
    <div>
        <span class="data-label">POLICY: RISK-SCALED BUFFER BUFFERING</span>
    </div>
</div>
""", unsafe_allow_html=True)

repo = get_repository()
inv_df = repo.get_inventory()
if inv_df.empty:
    seed_database(repo, seed=42)

inv_engine = InventoryEngine(repo)
portfolio_df = inv_engine.evaluate_inventory_portfolio()

# Top KPIs
critical_parts = int((portfolio_df["STOCKOUT_RISK_LEVEL"] == "CRITICAL").sum()) if not portfolio_df.empty else 0
avg_doc = float(portfolio_df["DAYS_OF_COVER"].mean()) if not portfolio_df.empty else 28.5
total_items = len(portfolio_df)

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_kpi("Critical Stockout Parts", f"{critical_parts} SKUs", subtext="Stockout Prob > 70%", data_label="calculated")
with k2:
    render_kpi("Portfolio Mean Cover", f"{avg_doc:.1f} Days", subtext="Target safety floor: 21d", data_label="calculated")
with k3:
    render_kpi("Monitored Parts", f"{total_items} Positions", subtext="Across 3 plant assembly hubs", data_label="observed")
with k4:
    render_kpi("Dynamic Risk Scaling", "+50% Max Buffer", subtext="k = 0.50 disclosed multiplier", data_label="assumption")

st.markdown("""<div style="margin-top: 1rem;"></div>""", unsafe_allow_html=True)

col_tbl, col_calc = st.columns([3, 2])

with col_tbl:
    st.markdown("### Parts Stockout Risk Matrix")
    if not portfolio_df.empty:
        disp_cols = ["MATERIAL_ID", "DESCRIPTION", "FACTORY_ID", "ON_HAND_QTY", "DAYS_OF_COVER", "BASE_SAFETY_STOCK", "RISK_AWARE_SAFETY_STOCK", "STOCKOUT_PROBABILITY", "STOCKOUT_RISK_LEVEL"]
        st.dataframe(portfolio_df[disp_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No inventory telemetry available.")

with col_calc:
    st.markdown("### Risk-Aware Buffer Scaling Simulator")
    st.markdown("""
    <div class="terminal-card">
        <div style="color: #9C9A96; font-size: 0.85rem; margin-bottom: 0.75rem;">
            Test how upstream supplier vulnerability forces inventory safety buffers to expand to prevent line stoppage.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    sim_base_safety = st.number_input("Base Safety Stock (Units)", min_value=50, max_value=5000, value=500, step=50)
    sim_risk = st.slider("Upstream Supplier Risk Score", min_value=0.0, max_value=1.0, value=0.75, step=0.05)
    
    scaled_safety = inv_engine.calculate_risk_aware_safety_stock(sim_base_safety, sim_risk)
    delta_units = scaled_safety - sim_base_safety
    
    st.markdown(f"""
    <div class="terminal-card" style="border-left: 4px solid {COLOR_RISK_WARNING}; margin-top: 1rem;">
        <div style="font-size: 0.8rem; color: #9C9A96;">REQUIRED BUFFER REQUIREMENT</div>
        <div style="font-size: 1.85rem; font-weight: 800; color: #F5F4F0; margin: 4px 0;">{scaled_safety:,.0f} Units</div>
        <div style="font-size: 0.85rem; color: {COLOR_RISK_WARNING};">
            ▲ +{delta_units:,.0f} Units (+{delta_units/sim_base_safety*100:.1f}%) risk hedge surcharge
        </div>
    </div>
    """, unsafe_allow_html=True)
