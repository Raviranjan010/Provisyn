"""PROVISYN — Architecture, Methodology & Attribution (Page 14).
System documentation, mathematical formulations, and dual legal attribution.
Strictly adheres to attribution_plan.md section 6, NOTICE, and LICENSE.
"""
import sys
from pathlib import Path
import streamlit as st

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
from backend.core.config import settings
from backend.data.repository import get_repository

st.set_page_config(page_title="PROVISYN — About & Methodology", layout="wide")
inject_provisyn_styles(st)
render_sidebar(current_page="About")

# Header Strip
st.markdown("""
<div style="border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: baseline;">
    <div>
        <h1 style="margin: 0; font-size: 1.75rem;">14 ABOUT & METHODOLOGY</h1>
        <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">System architecture, analytical formulation reference, and dual provenance attribution</div>
    </div>
    <div>
        <span class="data-label">VERSION: 2.0.0-PROVISYN</span>
        <span class="data-label">LICENSE: APACHE-2.0</span>
    </div>
</div>
""", unsafe_allow_html=True)

repo = get_repository()

# System Telemetry KPIs
k1, k2, k3, k4 = st.columns(4)
with k1:
    render_kpi("Data Backend", settings.DATA_BACKEND.upper(), subtext="BaseRepository driver", data_label="active")
with k2:
    render_kpi("Graph Backend", settings.GRAPH_BACKEND.upper(), subtext="Topology engine", data_label="active")
with k3:
    render_kpi("Decision Engines", "11 Active", subtext="Fully verified implementations", data_label="certified")
with k4:
    render_kpi("Design Standard", "Charcoal Flat", subtext="No gradients / zero blue", data_label="design.md")

st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

# 1. Core Mathematical Formulations
st.markdown("### 1. Mathematical Formulations & Analytical Foundations")

col_m1, col_m2 = st.columns(2)

with col_m1:
    st.markdown("""
    <div class="terminal-card" style="margin-bottom: 1rem; font-size: 0.85rem;">
        <div style="font-weight: 700; color: #F5F4F0; margin-bottom: 6px;">A. Multi-Tier Risk Propagation</div>
        <p style="color: #9C9A96; line-height: 1.5;">
            Upstream risks propagate downstream through directed Bills of Materials (BOM) edges with exponential dampening:
        </p>
        <code style="display: block; background: #1C1C1E; padding: 8px; border-radius: 4px; color: #F5F4F0; margin-bottom: 8px;">
            R_propagated(u) = α · R_base(u) + (1 - α) · Σ [ w_vu · R(v) · γ^tier ]
        </code>
        <div style="color: #9C9A96;">
            Where α = 0.60 (local score retention), w_vu is normalized supplier dependency share, and γ = 0.75 is attenuation per echelon hop.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="terminal-card" style="margin-bottom: 1rem; font-size: 0.85rem;">
        <div style="font-weight: 700; color: #F5F4F0; margin-bottom: 6px;">B. Prescriptive Mixed-Integer Optimization</div>
        <p style="color: #9C9A96; line-height: 1.5;">
            Solves optimal knapsack capital allocation across discrete interventions (dual-sourcing, buffer expansion, qualification):
        </p>
        <code style="display: block; background: #1C1C1E; padding: 8px; border-radius: 4px; color: #F5F4F0; margin-bottom: 8px;">
            max Σ (ExposureReduction_i + λ · ResilienceGain_i) · x_i<br>
            s.t. Σ Cost_i · x_i ≤ Budget,  x_i ∈ {0, 1}
        </code>
        <div style="color: #9C9A96;">
            Solved via PuLP COIN-OR CBC branch-and-cut linear programming.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_m2:
    st.markdown("""
    <div class="terminal-card" style="margin-bottom: 1rem; font-size: 0.85rem;">
        <div style="font-weight: 700; color: #F5F4F0; margin-bottom: 6px;">C. Risk-Aware Dynamic Safety Stock</div>
        <p style="color: #9C9A96; line-height: 1.5;">
            Augments classical inventory sizing with dynamic supplier failure probability:
        </p>
        <code style="display: block; background: #1C1C1E; padding: 8px; border-radius: 4px; color: #F5F4F0; margin-bottom: 8px;">
            SS_risk = Z_service · √(L · σ_d² + d² · σ_L²) · (1 + RiskScore_supplier)<br>
            ROP = d · L + SS_risk
        </code>
        <div style="color: #9C9A96;">
            Ensures safety buffers dynamically expand when upstream suppliers enter geopolitical or financial distress.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="terminal-card" style="margin-bottom: 1rem; font-size: 0.85rem;">
        <div style="font-weight: 700; color: #F5F4F0; margin-bottom: 6px;">D. Composite Portfolio Resilience Index</div>
        <p style="color: #9C9A96; line-height: 1.5;">
            Evaluates balanced organizational survivability across four orthogonal dimensions [0 - 100]:
        </p>
        <code style="display: block; background: #1C1C1E; padding: 8px; border-radius: 4px; color: #F5F4F0; margin-bottom: 8px;">
            Resilience = 25 · Redundancy + 25 · (1 - MeanRisk) + 25 · BufferCover + 25 · ExposureContainment
        </code>
        <div style="color: #9C9A96;">
            Penalizes unhedged concentration risks and single-point failure bottlenecks.
        </div>
    </div>
    """, unsafe_allow_html=True)

# 2. Dual Provenance & Attribution
st.markdown("### 2. Provenance, Authorship & Legal Attribution")

st.markdown("""
<div class="terminal-card" style="border-left: 4px solid #5B8266; font-size: 0.88rem; line-height: 1.6;">
    <div style="font-size: 1.05rem; font-weight: 700; color: #F5F4F0; margin-bottom: 8px;">
        Dual Authorship Notice (Per attribution_plan.md §6 & NOTICE)
    </div>
    <div style="margin-bottom: 8px;">
        <b>Built & Engineered by:</b> <span style="color: #F5F4F0; font-weight: 600;">Ravi Ranjan</span>
    </div>
    <div style="margin-bottom: 12px; color: #9C9A96;">
        Responsible for product vision, dual DuckDB/Snowflake architecture, 11 specialized decision engines 
        (Financial Exposure, Cascades, Digital Twin Simulations, Prescriptive PuLP Optimization, Dynamic Inventory), 
        XAI SHAP feature attribution, tool-grounded Decision Copilot, and the clean charcoal industrial design system.
    </div>
    <div style="border-top: 1px solid #3A3A3C; padding-top: 10px; margin-top: 10px;">
        <b>Foundational Architecture Credit:</b> <span style="color: #F5F4F0; font-weight: 600;">Snowflake Inc.</span>
    </div>
    <div style="color: #9C9A96;">
        PROVISYN is built upon the foundational graph concepts, schema structures, and analytical workflows from:
        <br>
        <a href="https://github.com/Snowflake-Labs/sfguide-supply-chain-risk-intelligence-with-snowflake" target="_blank" style="color: #F5F4F0; text-decoration: underline;">
            Snowflake-Labs / sfguide-supply-chain-risk-intelligence-with-snowflake
        </a>
        <br>
        <em>Copyright © Snowflake Inc. Licensed under the Apache License, Version 2.0.</em>
    </div>
</div>
""", unsafe_allow_html=True)

# 3. Licensing Disclaimer
st.markdown("### 3. Software License & Warranty Disclaimer")
st.markdown("""
<div class="terminal-card" style="font-size: 0.82rem; color: #9C9A96; line-height: 1.5;">
    <div><b>Apache License, Version 2.0</b></div>
    <div style="margin-top: 4px;">
        This application is licensed under the Apache License, Version 2.0. See <code>LICENSE</code> for the full legal text.
    </div>
    <div style="margin-top: 6px; font-style: italic;">
        This application is not part of the Snowflake Service and is governed by the terms in LICENSE, unless expressly agreed to in writing. 
        You use this application at your own risk, and Snowflake has no obligation to support your use of this application.
    </div>
</div>
""", unsafe_allow_html=True)
