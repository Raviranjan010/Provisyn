"""PROVISYN — Resilience Lab (Page 8).
Digital Twin scenario simulation, 7-stage disruption cascade, Monte Carlo uncertainty bounds (P10/P50/P90),
and before/after resilience score impact. Replaces Snowflake procedure ANALYZE_RISK_SCENARIO.
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
from frontend.components import render_kpi, render_cascade_stepper
from frontend.utils.sidebar import render_sidebar
from backend.data.repository import get_repository
from backend.data.generator import seed_database
from backend.engines.simulation import SimulationEngine, SCENARIO_TYPES
from backend.engines.resilience import ResilienceEngine

st.set_page_config(page_title="PROVISYN — Resilience Lab", layout="wide")
inject_provisyn_styles(st)
render_sidebar(current_page="Resilience Lab")

st.markdown("""
<div style="border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: baseline;">
    <div>
        <h1 style="margin: 0; font-size: 1.75rem;">08 RESILIENCE LAB & DIGITAL TWIN</h1>
        <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">Dynamic scenario simulation, 7-stage cascade traversal, and Monte Carlo P10/P50/P90 uncertainty analysis</div>
    </div>
    <div>
        <span class="data-label">SIMULATION ENGINE: MONTE CARLO N=100</span>
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

sim_engine = SimulationEngine(repo)
res_engine = ResilienceEngine(repo)

col_config, col_results = st.columns([1, 2])

with col_config:
    st.markdown("### Scenario Parameters")
    st.markdown('<div class="terminal-card">', unsafe_allow_html=True)
    
    scen_type = st.selectbox("Scenario Type", options=SCENARIO_TYPES, index=0)
    
    if "COUNTRY" in scen_type or "PORT" in scen_type:
        target = st.selectbox("Target Region", options=["AUS", "CHN", "COD", "CHL", "JPN", "USA", "DEU"])
        target_list = [target]
    elif scen_type == "MULTIPLE_SIMULTANEOUS_SUPPLIER_FAILURES":
        multi_sel = st.multiselect("Select Target Suppliers", options=active_vids, default=active_vids[:2])
        target_list = multi_sel if multi_sel else [active_vids[0]]
    else:
        single_target = st.selectbox("Target Supplier", options=active_vids, index=0)
        target_list = [single_target]
        
    intensity = st.slider("Shock Intensity", min_value=0.1, max_value=1.0, value=0.85, step=0.05)
    duration = st.slider("Duration (Days)", min_value=7, max_value=120, value=45, step=7)
    
    run_btn = st.button("Simulate Disruption", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Test Mitigation Intervention")
    st.markdown('<div class="terminal-card">', unsafe_allow_html=True)
    intervention_choice = st.selectbox(
        "Candidate Intervention",
        ["REGIONAL_DUAL_SOURCING", "INCREASE_SAFETY_STOCK", "ADD_ALTERNATE_SUPPLIER", "EXPEDITE_CONTRACT"]
    )
    inv_cost = st.number_input("Budget Investment ($)", min_value=10000, max_value=5000000, value=150000, step=25000)
    st.markdown('</div>', unsafe_allow_html=True)

# Run simulation
with col_results:
    sim_result = sim_engine.run_scenario(
        scenario_type=scen_type,
        target_entities=target_list,
        intensity=intensity,
        duration_days=duration,
        n_iterations=100
    )

    # Before / After KPIs
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi("Baseline Resilience", f"{sim_result.baseline_resilience:.1f}", subtext="Pre-shock index", data_label="calculated")
    with k2:
        render_kpi("Shock Resilience", f"{sim_result.projected_resilience:.1f}", subtext=f"Delta: {sim_result.resilience_delta} pts", data_label="simulated")
    with k3:
        render_kpi("Revenue at Risk", f"${sim_result.financial.revenue_at_risk/1e6:.2f}M", subtext=f"{len(sim_result.cascade.affected_orders)} orders impacted", data_label="simulated")
    with k4:
        render_kpi("Expected Loss", f"${sim_result.financial.expected_loss/1e6:.2f}M", subtext="Probability-weighted", data_label="calculated")

    st.markdown("""<div style="margin-top: 1rem;"></div>""", unsafe_allow_html=True)

    # 7-Stage Disruption Stepper
    st.markdown("### 7-Stage Disruption Cascade Trace")
    render_cascade_stepper(sim_result.cascade.stages)

    # Monte Carlo Uncertainty Bands
    st.markdown("### Monte Carlo Probabilistic Exposure (P10 / P50 / P90)")
    
    mc_fig = go.Figure()
    mc_fig.add_trace(go.Bar(
        y=["Financial Exposure"],
        x=[sim_result.monte_carlo_p10],
        name="P10 (Best Case)",
        orientation='h',
        marker_color=COLOR_RISK_HEALTHY,
        text=[f"P10: ${sim_result.monte_carlo_p10/1e6:.2f}M"],
        textposition="auto"
    ))
    mc_fig.add_trace(go.Bar(
        y=["Financial Exposure"],
        x=[sim_result.monte_carlo_p50 - sim_result.monte_carlo_p10],
        name="P50 (Median Case)",
        orientation='h',
        marker_color=COLOR_RISK_WARNING,
        text=[f"P50: ${sim_result.monte_carlo_p50/1e6:.2f}M"],
        textposition="auto"
    ))
    mc_fig.add_trace(go.Bar(
        y=["Financial Exposure"],
        x=[sim_result.monte_carlo_p90 - sim_result.monte_carlo_p50],
        name="P90 (Worst Case)",
        orientation='h',
        marker_color=COLOR_RISK_CRITICAL,
        text=[f"P90: ${sim_result.monte_carlo_p90/1e6:.2f}M"],
        textposition="auto"
    ))

    mc_fig.update_layout(
        barmode='stack',
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=COLOR_SURFACE,
        height=180,
        margin=dict(l=30, r=20, t=10, b=30),
        xaxis=dict(tickformat="$,.0f", gridcolor=COLOR_BORDER, tickfont=dict(color=COLOR_TEXT_PRIMARY)),
        yaxis=dict(showticklabels=False),
        showlegend=True,
        legend=dict(font=dict(color=COLOR_TEXT_PRIMARY), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(mc_fig, use_container_width=True)

    # Intervention evaluation delta
    int_eval = res_engine.evaluate_intervention(
        baseline_score=sim_result.projected_resilience,
        intervention_type=intervention_choice,
        investment_cost=float(inv_cost)
    )
    
    st.markdown(f"""
    <div class="terminal-card" style="border-left: 4px solid {COLOR_RISK_HEALTHY}; margin-top: 1rem;">
        <div style="font-weight: 700; font-size: 0.95rem; color: #F5F4F0; margin-bottom: 4px;">PROJECTED INTERVENTION RECOVERY</div>
        <div style="color: #9C9A96; font-size: 0.85rem;">
            Applying <strong>{intervention_choice}</strong> ($ {inv_cost:,.0f} allocated) restores resilience from 
            <strong>{int_eval['baseline_score']:.1f}</strong> to <strong>{int_eval['new_score']:.1f}</strong> 
            (<span style="color: {COLOR_RISK_HEALTHY}; font-weight: 600;">▲ +{int_eval['delta']:.1f} pts</span>).
        </div>
    </div>
    """, unsafe_allow_html=True)
