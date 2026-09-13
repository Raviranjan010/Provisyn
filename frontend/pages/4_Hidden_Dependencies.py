"""PROVISYN — Hidden Dependencies (Page 4).
Uncovering undisclosed Tier-2+ supply chain dependencies and Single Points of Failure (SPOF).
Ported from Tier-2 Analysis page and setup_networkx.sql compatibility views.
"""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

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
from frontend.components import render_kpi, render_risk_badge, render_alert_item
from frontend.utils.sidebar import render_sidebar
from backend.data.repository import get_repository
from backend.data.generator import seed_database
from backend.engines.hidden_dependency import HiddenDependencyEngine
from backend.engines.spof import SPOFEngine

st.set_page_config(page_title="PROVISYN — Hidden Dependencies", layout="wide")
inject_provisyn_styles(st)
render_sidebar(current_page="Hidden Dependencies")

st.markdown("""
<div style="border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: baseline;">
    <div>
        <h1 style="margin: 0; font-size: 1.75rem;">04 HIDDEN DEPENDENCIES & SPOF</h1>
        <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">Inferring undisclosed Tier-2+ suppliers from global trade data flows and detecting Single Points of Failure</div>
    </div>
    <div>
        <span class="data-label">DISCOVERY: TRADE DATA + JACCARD SIMILARITY</span>
    </div>
</div>
""", unsafe_allow_html=True)

repo = get_repository()
vendors_df = repo.get_vendors()
if vendors_df.empty:
    seed_database(repo, seed=42)

hidden_engine = HiddenDependencyEngine(repo)
spof_engine = SPOFEngine(repo)

df_hidden = repo.get_predicted_links()
if df_hidden.empty:
    df_hidden = hidden_engine.discover_hidden_dependencies()

df_spof = repo.get_bottlenecks()
if df_spof.empty:
    df_spof = spof_engine.identify_bottlenecks()

# Top KPIs
total_predicted = len(df_hidden) if not df_hidden.empty else 0
critical_spofs = int((df_spof["SEVERITY_TIER"] == "CRITICAL").sum()) if not df_spof.empty else 0
total_impact = float(df_hidden["FINANCIAL_IMPACT"].sum()) if not df_hidden.empty and "FINANCIAL_IMPACT" in df_hidden.columns else 0.0

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_kpi("Inferred Dependencies", f"{total_predicted} Links", subtext="From trade bills of lading", data_label="calculated")
with k2:
    render_kpi("Critical Bottlenecks", f"{critical_spofs} SPOFs", subtext="Sole source / Zero redundancy", data_label="calculated")
with k3:
    render_kpi("Hidden Value at Risk", f"${total_impact/1e6:.2f}M", subtext="Unhedged indirect spend", data_label="simulated")
with k4:
    render_kpi("Inference Confidence", "94% Peak", subtext="Outback Lithium pattern verified", data_label="observed")

st.markdown("""<div style="margin-top: 1rem;"></div>""", unsafe_allow_html=True)

# Synthetic Storyline Banner
st.markdown("""
<div class="terminal-card" style="border-left: 4px solid #C99A3B;">
    <div style="font-weight: 700; color: #F5F4F0; margin-bottom: 4px;">SYNTHETIC DISCOVERY CASE: The Illusion of Diversity (Outback Lithium Resources)</div>
    <div style="color: #9C9A96; font-size: 0.85rem; line-height: 1.5;">
        While your direct ERP records show multi-vendor sourcing across 12 distinct battery tier manufacturers in South Korea, China, and Japan,
        PROVISYN's trade data link-inference engine reveals that <strong>85% of these suppliers depend on a single Australian mining extractor (Outback Lithium Resources)</strong>.
        A disruption at this single upstream facility cascades across your entire Tier-1 portfolio simultaneously.
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Discovered Tier-2+ Dependencies", "SPOF Bottleneck Rankings"])

with tab1:
    st.markdown("### Trade-Inferred Supply Chain Links")
    if not df_hidden.empty:
        disp_cols = ["SOURCE_ID", "TARGET_ID", "SIMILARITY_SCORE", "CONFIDENCE", "CRITICALITY", "FINANCIAL_IMPACT", "EVIDENCE"]
        show_df = df_hidden[[c for c in disp_cols if c in df_hidden.columns]].sort_values(by="SIMILARITY_SCORE", ascending=False)
        st.dataframe(show_df, use_container_width=True, hide_index=True)
    else:
        st.info("No hidden links found.")

with tab2:
    st.markdown("### Single Points of Failure & Redundancy Analysis")
    if not df_spof.empty:
        disp_spof = ["BOTTLENECK_RANK", "ENTITY_TYPE", "ENTITY_ID", "SEVERITY_TIER", "BETWEENNESS_SCORE", "ALTERNATIVE_PATH_COUNT", "AFFECTED_NETWORK_SIZE", "RISK_SCORE"]
        st.dataframe(df_spof[[c for c in disp_spof if c in df_spof.columns]], use_container_width=True, hide_index=True)
    else:
        st.info("No bottlenecks identified.")
