"""PROVISYN — Risk Intelligence (Page 2).
Multi-dimensional risk quantification across 10 risk dimensions.
Ported from exploratory analysis & notebook risk propagation + supervised risk regressor.
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
from frontend.components import render_kpi, render_risk_badge
from frontend.utils.sidebar import render_sidebar
from backend.data.repository import get_repository
from backend.data.generator import seed_database
from backend.engines.risk import RiskEngine

st.set_page_config(page_title="PROVISYN — Risk Intelligence", layout="wide")
inject_provisyn_styles(st)
render_sidebar(current_page="Risk Intelligence")

# Header Strip
st.markdown("""
<div style="border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: baseline;">
    <div>
        <h1 style="margin: 0; font-size: 1.75rem;">02 RISK INTELLIGENCE</h1>
        <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">Multi-tier risk quantification across 10 supply chain risk dimensions with SHAP explainability</div>
    </div>
    <div>
        <span class="data-label">METHOD: GRAPH PROPAGATION + GBR</span>
    </div>
</div>
""", unsafe_allow_html=True)

repo = get_repository()
engine = RiskEngine(repo)

# Ensure database is seeded with data if empty
vendors = repo.get_vendors()
if vendors.empty:
    seed_database(repo, seed=42)

df_risk = repo.get_risk_scores()
if df_risk.empty:
    with st.spinner("Computing initial multi-tier risk scores..."):
        df_risk = engine.compute_risk_scores()

# Top KPI Strip
avg_risk = float(df_risk["RISK_SCORE"].mean()) if not df_risk.empty else 0.52
critical_count = int((df_risk["RISK_CATEGORY"] == "CRITICAL").sum()) if not df_risk.empty else 0
high_count = int((df_risk["RISK_CATEGORY"] == "HIGH").sum()) if not df_risk.empty else 0
total_exposure = float(df_risk["FINANCIAL_EXPOSURE"].sum()) if not df_risk.empty else 0.0

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_kpi("Portfolio Mean Risk", f"{avg_risk:.3f}", subtext="Scale [0.0 - 1.0]", data_label="calculated")
with k2:
    render_kpi("Critical Entities", f"{critical_count} Nodes", subtext=f"High Risk: {high_count}", data_label="calculated")
with k3:
    render_kpi("Aggregate Exposure", f"${total_exposure/1e6:.2f}M", subtext="Capacity-at-risk weighted", data_label="calculated")
with k4:
    render_kpi("Model Explainability", "88% PR-AUC", subtext="v1.2.0-provisyn active", data_label="observed")

st.markdown("""<div style="margin-top: 1rem;"></div>""", unsafe_allow_html=True)

# Filters Row
fc1, fc2, fc3 = st.columns([2, 2, 4])
with fc1:
    entity_filter = st.selectbox("Entity Type", ["ALL", "VENDOR", "MATERIAL"], index=0)
with fc2:
    category_filter = st.selectbox("Risk Level", ["ALL", "CRITICAL", "HIGH", "WARNING", "HEALTHY"], index=0)
with fc3:
    search_query = st.text_input("Search Entity Name or ID", "")

filtered_df = df_risk.copy()
if entity_filter != "ALL":
    filtered_df = filtered_df[filtered_df["ENTITY_TYPE"] == entity_filter]
if category_filter != "ALL":
    filtered_df = filtered_df[filtered_df["RISK_CATEGORY"] == category_filter]
if search_query:
    filtered_df = filtered_df[
        filtered_df["ENTITY_ID"].str.contains(search_query, case=False, na=False) |
        filtered_df["NAME"].str.contains(search_query, case=False, na=False)
    ]

# Layout: Chart + Table
col_chart, col_explain = st.columns([3, 2])

with col_chart:
    st.markdown("### Risk Score Distribution")
    cat_counts = df_risk["RISK_CATEGORY"].value_counts()
    categories_order = ["HEALTHY", "WARNING", "HIGH", "CRITICAL"]
    counts = [int(cat_counts.get(c, 0)) for c in categories_order]
    bar_colors = [COLOR_RISK_HEALTHY, COLOR_RISK_WARNING, COLOR_RISK_HIGH, COLOR_RISK_CRITICAL]

    fig = go.Figure(data=[
        go.Bar(
            x=categories_order,
            y=counts,
            marker_color=bar_colors,
            text=counts,
            textposition="auto"
        )
    ])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=COLOR_SURFACE,
        height=280,
        margin=dict(l=30, r=20, t=20, b=30),
        xaxis=dict(gridcolor=COLOR_BORDER, tickfont=dict(color=COLOR_TEXT_PRIMARY)),
        yaxis=dict(gridcolor=COLOR_BORDER, tickfont=dict(color=COLOR_TEXT_SECONDARY)),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_explain:
    st.markdown("### Explainable AI — Risk Driver Breakdown")
    selected_entity_id = st.selectbox(
        "Select Entity to Inspect Drivers",
        options=filtered_df["ENTITY_ID"].tolist() if not filtered_df.empty else ["V10001"]
    )
    explanation = engine.explain_entity_risk(selected_entity_id)
    
    st.markdown(f"""
    <div class="terminal-card">
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
            <span style="font-weight: 700; font-size: 1.05rem;">{explanation.get('name', selected_entity_id)}</span>
            {render_risk_badge(explanation.get('category', 'WARNING'))}
        </div>
        <div style="font-size: 0.8rem; color: #9C9A96; margin-bottom: 12px;">ID: <span class="code-id">{selected_entity_id}</span> • Score: {explanation.get('total_score', 0):.4f}</div>
    """, unsafe_allow_html=True)
    
    for d in explanation.get("drivers", []):
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #3A3A3C; font-size: 0.85rem;">
            <span>{d['factor']} <br><small style="color: #9C9A96;">{d['description']}</small></span>
            <span style="color: {COLOR_RISK_WARNING}; font-weight: 600; font-family: monospace;">{d['impact']}</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("### Risk Rankings & Exposure Portfolio")
table_cols = ["ENTITY_ID", "ENTITY_TYPE", "NAME", "COUNTRY_CODE", "RISK_SCORE", "RISK_CATEGORY", "FAILURE_PROBABILITY", "FINANCIAL_EXPOSURE"]
display_df = filtered_df[[c for c in table_cols if c in filtered_df.columns]].sort_values("RISK_SCORE", ascending=False)
st.dataframe(display_df, use_container_width=True, hide_index=True)
