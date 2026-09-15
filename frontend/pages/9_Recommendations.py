"""PROVISYN — Recommendations (Page 9).
Optimization-ranked prescriptive mitigation actions and interventions.
Solves Knapsack / Mixed-Integer Linear Programming (MILP) via PuLP across candidate actions.
Strictly adheres to design.md (flat industrial terminal, no gradients, no blue).
"""
import sys
import json
from pathlib import Path
from datetime import datetime
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
from frontend.components import render_kpi, render_risk_badge, render_data_label
from frontend.utils.sidebar import render_sidebar
from backend.data.repository import get_repository
from backend.data.generator import seed_database
from backend.engines.optimization import OptimizationEngine
from backend.engines.recommendation import RecommendationEngine

st.set_page_config(page_title="PROVISYN — Recommendations", layout="wide")
inject_provisyn_styles(st)
render_sidebar(current_page="Recommendations")

# Header Strip
st.markdown("""
<div style="border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: baseline;">
    <div>
        <h1 style="margin: 0; font-size: 1.75rem;">09 RECOMMENDATIONS & MITIGATION</h1>
        <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">Mathematically optimal capital allocation for risk mitigation using Mixed-Integer Linear Programming</div>
    </div>
    <div>
        <span class="data-label">SOLVER: PuLP CBC / COIN-OR</span>
    </div>
</div>
""", unsafe_allow_html=True)

repo = get_repository()
vendors_df = repo.get_vendors()
if vendors_df.empty:
    seed_database(repo, seed=42)

rec_engine = RecommendationEngine(repo)
opt_engine = OptimizationEngine(repo)

# Control Bar: Budget Allocation
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 2, 1])

with col_ctrl1:
    budget_input = st.slider(
        "Capital Expenditure Mitigation Budget (USD)",
        min_value=50000,
        max_value=2500000,
        value=500000,
        step=25000,
        format="$%d"
    )

with col_ctrl2:
    optimization_goal = st.selectbox(
        "Optimization Objective",
        options=[
            "Balanced: Exposure & Resilience Improvement",
            "Maximum Financial Exposure Reduction",
            "Maximum Network Resilience Gain",
        ]
    )

with col_ctrl3:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    solve_btn = st.button("Re-solve Portfolio", type="primary", use_container_width=True)

# Run Optimization
opt_result = rec_engine.generate_recommendations(budget=float(budget_input))

# KPI Strip
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    render_kpi("Capital Budget", f"${budget_input:,.0f}", subtext="Constraint ceiling", data_label="parameter")
with kpi2:
    spend_val = f"${opt_result['total_spend']:,.0f}" if opt_result['is_feasible'] else "$0"
    render_kpi("Allocated Spend", spend_val, subtext=f"{(opt_result['total_spend']/budget_input*100):.1f}% utilized" if opt_result['is_feasible'] else "Unallocated", data_label="calculated")
with kpi3:
    exp_val = f"${opt_result['exposure_reduction']:,.0f}" if opt_result['is_feasible'] else "$0"
    render_kpi("Exposure Avoidance", exp_val, subtext="Downstream revenue loss saved", data_label="simulated")
with kpi4:
    res_val = f"+{opt_result['resilience_gain']:.1f} pts" if opt_result['is_feasible'] else "0.0 pts"
    render_kpi("Resilience Delta", res_val, subtext="Composite score increase", data_label="calculated")
with kpi5:
    status_text = "OPTIMAL" if opt_result['is_feasible'] else "INFEASIBLE"
    render_kpi("Solver Status", status_text, subtext=opt_result['message'][:24], data_label="solver")

st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

# Main Recommendations Table & Detail Cards
selected_actions = opt_result.get("recommendations", [])

if selected_actions:
    st.markdown("### Prescriptive Action Portfolio (Ranked by Return on Resilience)")

    rec_rows = []
    for a in selected_actions:
        rec_rows.append({
            "Rank": a["rank"],
            "Action Title": a["title"],
            "Type": a["action_type"].replace("_", " "),
            "Target Entity": a["target_entity"],
            "Cost (USD)": f"${a['estimated_cost']:,.0f}",
            "Risk Reduction": f"-{a['risk_reduction']:.1f} pts",
            "Exposure Reduction": f"${a['exposure_reduction']:,.0f}",
            "Resilience Gain": f"+{a['resilience_improvement']:.1f} pts",
            "Recovery Time": f"-{a['recovery_days_improvement']} days",
            "Confidence": f"{int(a['confidence'] * 100)}%"
        })

    df_display = pd.DataFrame(rec_rows)
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Detailed Cards for Each Action
    st.markdown("#### Action Implementation Briefings")
    cols = st.columns(min(len(selected_actions), 3))
    for idx, act in enumerate(selected_actions):
        col = cols[idx % 3]
        with col:
            st.markdown(f"""
            <div class="terminal-card" style="border-left: 3px solid {COLOR_RISK_HEALTHY}; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px;">
                    <span class="code-id">#{act['rank']} {act['action_id']}</span>
                    <span class="data-label">{act['action_type']}</span>
                </div>
                <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 6px; color: #F5F4F0;">
                    {act['title']}
                </div>
                <div style="font-size: 0.85rem; color: #9C9A96; margin-bottom: 8px;">
                    Target: <code class="code-id">{act['target_entity']}</code> &nbsp;|&nbsp; Confidence: {int(act['confidence']*100)}%
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 0.8rem; background: #1C1C1E; padding: 6px 8px; border-radius: 4px;">
                    <div>Cost: <b style="color: #F5F4F0;">${act['estimated_cost']:,.0f}</b></div>
                    <div>Exposure Saved: <b style="color: {COLOR_RISK_HEALTHY};">${act['exposure_reduction']:,.0f}</b></div>
                    <div>Risk Impact: <b style="color: {COLOR_RISK_HEALTHY};">-{act['risk_reduction']:.1f} pts</b></div>
                    <div>MTTR Impact: <b style="color: #F5F4F0;">-{act['recovery_days_improvement']}d</b></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Decision Commitment
    st.markdown("### Operational Decision Commitment")
    col_dec1, col_dec2 = st.columns([3, 1])
    with col_dec1:
        st.markdown(
            "Committing this portfolio records an auditable entry in `DECISION_HISTORY` and locks "
            "the capital allocation for the operational quarter."
        )
    with col_dec2:
        if st.button("Commit Mitigation Portfolio", type="primary", use_container_width=True):
            decision_record = {
                "DECISION_ID": f"DEC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "TITLE": f"Approved Mitigation Portfolio (${opt_result['total_spend']:,.0f})",
                "ACTION_TAKEN": f"Executed {len(selected_actions)} interventions under budget ${budget_input:,.0f}",
                "BEFORE_STATE_JSON": json.dumps({"budget": budget_input}),
                "AFTER_STATE_JSON": json.dumps({
                    "total_spend": opt_result["total_spend"],
                    "exposure_saved": opt_result["exposure_reduction"],
                    "resilience_delta": opt_result["resilience_gain"],
                    "actions": [a["action_id"] for a in selected_actions]
                }),
                "RESILIENCE_DELTA": opt_result["resilience_gain"],
                "DECIDED_BY": "Supply Chain Operations Lead",
                "DECIDED_AT": datetime.now()
            }
            repo.write_table(pd.DataFrame([decision_record]), "DECISION_HISTORY", overwrite=False)
            st.success("Decision committed and recorded in auditable DECISION_HISTORY log.")

else:
    st.warning("No actions fit within current budget constraint. Increase capital allocation to solve.")

# Candidate Action Pool & Solver Sensitivity
st.markdown("### Candidate Action Pool & Return-on-Investment")
all_candidates = opt_engine.DEFAULT_CANDIDATES
cand_rows = []
for c in all_candidates:
    is_sel = any(a["action_id"] == c.action_id for a in selected_actions)
    roi_exposure = c.exposure_reduction / max(1.0, c.estimated_cost)
    cand_rows.append({
        "Action ID": c.action_id,
        "Title": c.title,
        "Type": c.action_type,
        "Target": c.target_entity,
        "Cost": f"${c.estimated_cost:,.0f}",
        "Exposure Saved": f"${c.exposure_reduction:,.0f}",
        "Resilience Gain": f"+{c.resilience_improvement:.1f}",
        "ROI ($ Saved / $ Spent)": f"{roi_exposure:.2f}x",
        "Selected in Solution": "YES" if is_sel else "EXCLUDED (Budget)"
    })

st.dataframe(pd.DataFrame(cand_rows), use_container_width=True, hide_index=True)
