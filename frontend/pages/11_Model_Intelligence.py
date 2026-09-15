"""PROVISYN — Model Intelligence & Governance (Page 11).
Model registry, evaluation telemetry, training pipeline, and feature importance attribution.
Strictly surfaces synthetic demo labels vs. authentic trained model performance per P0-3 and P1-1.
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
from ml.risk.train import train_and_register_risk_models

st.set_page_config(page_title="PROVISYN — Model Intelligence", layout="wide")
inject_provisyn_styles(st)
render_sidebar(current_page="Model Intelligence")

# Header Strip
st.markdown("""
<div style="border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: baseline;">
    <div>
        <h1 style="margin: 0; font-size: 1.75rem;">11 MODEL INTELLIGENCE & GOVERNANCE</h1>
        <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">Predictive model registry, genuine cross-validation metrics, and feature importance attribution</div>
    </div>
    <div>
        <span class="data-label">FRAMEWORK: SCIKIT-LEARN / XGBOOST</span>
        <span class="data-label">EXPLAINABILITY: SHAP</span>
    </div>
</div>
""", unsafe_allow_html=True)

repo = get_repository()
vendors_df = repo.get_vendors()
if vendors_df.empty:
    seed_database(repo, seed=42)

models_df = repo.get_model_versions()

# Top Action Strip: Model Training Controller
col_hdr1, col_hdr2 = st.columns([3, 1])
with col_hdr1:
    st.markdown("""
    PROVISYN strictly adheres to **Part 25 zero-fabrication standards**. If models have not been trained on local data, 
    rows are explicitly tagged with `SYNTHETIC_DEMO`. Trigger the pipeline below to train live models on current operational and graph features.
    """)
with col_hdr2:
    if st.button("Train Supervised Models", type="primary", use_container_width=True):
        with st.spinner("Extracting operational & graph features and training models..."):
            pipeline = train_and_register_risk_models(repo)
            st.success("Successfully trained RiskScoreRegressor and FailureProbabilityClassifier!")
            st.rerun()

# Model Registry Overview
st.markdown("### Registered Models in Enterprise Repository")

if models_df.empty:
    st.info("No registered models found in repository. Click 'Train Supervised Models' to initialize.")
else:
    # Summary Cards
    trained_count = len(models_df[models_df.get("STATUS", "") == "TRAINED_ACTIVE"])
    demo_count = len(models_df[models_df.get("STATUS", "") == "SYNTHETIC_DEMO"])

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi("Registered Models", str(len(models_df)), subtext="In governance registry", data_label="observed")
    with k2:
        render_kpi("Authentic Trained", str(trained_count), subtext="Validated on train/test split", data_label="calculated")
    with k3:
        render_kpi("Demo Placeholders", str(demo_count), subtext="Awaiting training pipeline", data_label="synthetic")
    with k4:
        active_status = "CERTIFIED" if trained_count > 0 else "DEMO MODE"
        render_kpi("Registry Status", active_status, subtext="Zero-fabrication compliance", data_label="audit")

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # Detailed Cards for Each Model
    for _, m in models_df.iterrows():
        status = str(m.get("STATUS", "UNKNOWN"))
        is_synthetic = status == "SYNTHETIC_DEMO"
        border_col = COLOR_RISK_WARNING if is_synthetic else COLOR_RISK_HEALTHY
        status_label = "SYNTHETIC DEMO PLACEHOLDER" if is_synthetic else "ACTIVE TRAINED MODEL"
        
        # Parse Metrics JSON
        metrics = {}
        try:
            raw_m = m.get("METRICS_JSON", "{}")
            if isinstance(raw_m, str):
                metrics = json.loads(raw_m)
            elif isinstance(raw_m, dict):
                metrics = raw_m
        except Exception:
            metrics = {}

        st.markdown(f"""
        <div class="terminal-card" style="border-left: 4px solid {border_col}; margin-bottom: 1.25rem;">
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px;">
                <div>
                    <strong style="font-size: 1.1rem; color: #F5F4F0;">{m.get('MODEL_NAME', 'Model')}</strong>
                    <span class="code-id" style="margin-left: 8px;">v{m.get('VERSION', '1.0.0')}</span>
                </div>
                <span class="data-label" style="background: {'#3D2E12' if is_synthetic else '#1C3322'}; color: {'#EAB308' if is_synthetic else '#4ADE80'};">
                    {status_label}
                </span>
            </div>
            <div style="color: #9C9A96; font-size: 0.85rem; margin-bottom: 8px;">
                Dataset: <code class="code-id">{m.get('DATASET_VERSION', 'N/A')}</code> &nbsp;•&nbsp; 
                Training Date: {str(m.get('TRAINING_DATE', 'N/A'))[:19]} &nbsp;•&nbsp;
                Note: <em>{m.get('NOTE', 'None')}</em>
            </div>
        """, unsafe_allow_html=True)

        # Render Metrics Grid
        if metrics:
            metric_cols = st.columns(min(4, len(metrics)))
            idx = 0
            for k, v in metrics.items():
                if k == "feature_importances":
                    continue
                with metric_cols[idx % len(metric_cols)]:
                    val_str = f"{v:.4f}" if isinstance(v, float) else str(v)
                    st.metric(label=k.replace("_", " ").upper(), value=val_str)
                idx += 1

            # If feature importances exist, render horizontal bar chart
            if "feature_importances" in metrics and isinstance(metrics["feature_importances"], dict):
                st.markdown("<div style='font-size: 0.85rem; font-weight: 600; margin-top: 10px;'>Top Feature Contributions:</div>", unsafe_allow_html=True)
                fi_data = sorted(metrics["feature_importances"].items(), key=lambda x: x[1], reverse=True)
                feats = [x[0].replace("_", " ").title() for x in fi_data][:6]
                scores = [x[1] for x in fi_data][:6]

                fig = go.Figure(go.Bar(
                    x=scores[::-1],
                    y=feats[::-1],
                    orientation="h",
                    marker_color=COLOR_RISK_HEALTHY,
                ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor=COLOR_SURFACE,
                    height=200,
                    margin=dict(l=150, r=20, t=10, b=20),
                    xaxis=dict(gridcolor=COLOR_BORDER, tickfont=dict(color=COLOR_TEXT_SECONDARY)),
                    yaxis=dict(tickfont=dict(color=COLOR_TEXT_PRIMARY, size=11)),
                )
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

# Governance & Verification Rules
st.markdown("### Governance & Verification Standards")
st.markdown(f"""
<div class="terminal-card" style="font-size: 0.85rem; line-height: 1.6;">
    <div><b>1. Zero Metric Fabrication:</b> All model metrics in PROVISYN are either computed over authentic <code>train_test_split</code> subsets or explicitly stamped as <code>SYNTHETIC_DEMO</code>.</div>
    <div><b>2. Deterministic Reproducibility:</b> Model training pipelines enforce seed consistency (<code>random_state=42</code>) across tree depth, bagging fractions, and split partitions.</div>
    <div><b>3. SHAP Additivity:</b> Explainable AI drivers decompose total prediction scores into exact additive components, preventing unexplained black-box supplier flags.</div>
</div>
""", unsafe_allow_html=True)
