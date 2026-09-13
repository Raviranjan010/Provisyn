"""PROVISYN — Financial Exposure (Page 6).
Financial disruption quantification: Revenue at Risk, Production Loss, Expediting Premiums, and Expected Loss.
Strict adherence to explicit labeling: observed, calculated, simulated, or assumption.
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
    COLOR_RISK_HIGH,
    COLOR_RISK_CRITICAL,
)
from frontend.components import render_kpi, render_data_label
from frontend.utils.sidebar import render_sidebar
from backend.data.repository import get_repository
from backend.data.generator import seed_database
from backend.engines.financial import FinancialExposureEngine

st.set_page_config(page_title="PROVISYN — Financial Exposure", layout="wide")
inject_provisyn_styles(st)
render_sidebar(current_page="Financial Exposure")

st.markdown("""
<div style="border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: baseline;">
    <div>
        <h1 style="margin: 0; font-size: 1.75rem;">06 FINANCIAL EXPOSURE</h1>
        <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">P&L disruption quantification, revenue-at-risk, production downtime, and recovery costs with strict labeling</div>
    </div>
    <div>
        <span class="data-label">FINANCIAL ENGINE: MULTI-STAGE EXPOSURE</span>
    </div>
</div>
""", unsafe_allow_html=True)

repo = get_repository()
vendors_df = repo.get_vendors()
if vendors_df.empty:
    seed_database(repo, seed=42)
    vendors_df = repo.get_vendors()

po_df = repo.get_purchase_orders()
active_vids = po_df["VENDOR_ID"].unique().tolist() if not po_df.empty else vendors_df["VENDOR_ID"].tolist()

financial_engine = FinancialExposureEngine(repo)

# Simulation controls
ctrl1, ctrl2, ctrl3 = st.columns([3, 2, 2])
with ctrl1:
    selected_seed = st.selectbox(
        "Select Shock Target Supplier",
        options=active_vids,
        index=0
    )
with ctrl2:
    shock_sev = st.slider("Disruption Severity", min_value=0.1, max_value=1.0, value=0.75, step=0.05)
with ctrl3:
    prob_val = st.slider("Disruption Probability", min_value=0.05, max_value=1.0, value=0.30, step=0.05)

fin_res = financial_engine.calculate_exposure(
    seed_entities=[selected_seed],
    shock_severity=shock_sev,
    disruption_probability=prob_val
)

# Top KPI Strip (With explicit labels on EVERY metric)
k1, k2, k3, k4 = st.columns(4)
with k1:
    render_kpi("Revenue at Risk", f"${fin_res.revenue_at_risk/1e6:.2f}M", subtext="Customer orders impacted", data_label="simulated")
with k2:
    render_kpi("Production Losses", f"${fin_res.production_loss/1e3:,.0f}", subtext="Factory capacity downtime", data_label="calculated")
with k3:
    render_kpi("Expediting Premium", f"${fin_res.expediting_cost/1e3:,.0f}", subtext="15% expedited freight", data_label="assumption")
with k4:
    render_kpi("Expected Loss", f"${fin_res.expected_loss/1e6:.2f}M", subtext=f"P(shock) = {prob_val*100:.0f}%", data_label="calculated")

st.markdown("""<div style="margin-top: 1rem;"></div>""", unsafe_allow_html=True)

# Breakdown Layout
col_chart, col_orders = st.columns([2, 3])

with col_chart:
    st.markdown("### Financial Cost Component Breakdown")
    cost_names = ["Revenue at Risk", "Production Loss", "Holding Cost", "Expediting Freight", "Recovery Price Delta"]
    cost_values = [
        fin_res.revenue_at_risk,
        fin_res.production_loss,
        fin_res.holding_cost,
        fin_res.expediting_cost,
        fin_res.recovery_cost
    ]
    cost_labels = [
        fin_res.labels.get("revenue_at_risk", "simulated"),
        fin_res.labels.get("production_loss", "calculated"),
        fin_res.labels.get("holding_cost", "calculated"),
        fin_res.labels.get("expediting_cost", "assumption"),
        fin_res.labels.get("recovery_cost", "calculated")
    ]
    
    fig = go.Figure(data=[
        go.Bar(
            x=cost_names,
            y=cost_values,
            marker_color=[COLOR_RISK_CRITICAL, COLOR_RISK_HIGH, COLOR_RISK_WARNING, "#9C9A96", COLOR_RISK_HEALTHY],
            text=[f"${v:,.0f}" for v in cost_values],
            textposition="auto"
        )
    ])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=COLOR_SURFACE,
        height=320,
        margin=dict(l=30, r=20, t=20, b=60),
        xaxis=dict(tickangle=-25, tickfont=dict(color=COLOR_TEXT_PRIMARY, size=10)),
        yaxis=dict(gridcolor=COLOR_BORDER, tickfont=dict(color=COLOR_TEXT_SECONDARY)),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_orders:
    st.markdown("### Orders Directly Vulnerable to Disruption")
    if fin_res.affected_orders:
        orders_df_show = pd.DataFrame(fin_res.affected_orders)
        orders_df_show["revenue"] = orders_df_show["revenue"].apply(lambda r: f"${r:,.0f}")
        orders_df_show = orders_df_show.rename(columns={
            "order_id": "Order ID",
            "customer_id": "Customer Account",
            "product_id": "Product ID",
            "revenue": "Revenue ($)",
            "quantity": "Units",
            "due_date": "Due Date"
        })
        st.dataframe(orders_df_show, use_container_width=True, hide_index=True)
    else:
        st.info("No customer purchase commitments impacted under current disruption parameters.")
