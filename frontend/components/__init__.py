"""Shared UI components for PROVISYN.
Designed with strict flat, industrial terminal aesthetic (no gradients, no glassmorphism, no blue).
"""
import streamlit as st
from frontend.components.styles import (
    inject_provisyn_styles,
    COLOR_RISK_HEALTHY,
    COLOR_RISK_WARNING,
    COLOR_RISK_HIGH,
    COLOR_RISK_CRITICAL,
)

def render_kpi(label: str, value: str, subtext: str = "", delta: str = None, data_label: str = None):
    """Render a flat, high-contrast KPI tile with optional data label (observed/calculated/simulated/assumption)."""
    badge_html = f'<span class="data-label">{data_label}</span>' if data_label else ""
    delta_html = f'<span class="kpi-subtext" style="color: {COLOR_RISK_WARNING};">{delta}</span>' if delta else ""
    subtext_html = f'<div class="kpi-subtext">{subtext} {delta_html}</div>' if (subtext or delta) else ""
    
    st.markdown(f"""
    <div class="kpi-tile">
        <div class="kpi-label">{label} {badge_html}</div>
        <div class="kpi-value">{value}</div>
        {subtext_html}
    </div>
    """, unsafe_allow_html=True)

def render_risk_badge(level: str):
    """Render a semantic risk badge (CRITICAL / HIGH / WARNING / HEALTHY)."""
    clean_level = str(level).strip().upper()
    if clean_level in ["CRITICAL", "RED", "HIGH RISK"]:
        css_class = "risk-badge-critical"
    elif clean_level in ["HIGH", "ORANGE"]:
        css_class = "risk-badge-high"
    elif clean_level in ["WARNING", "MEDIUM", "MODERATE", "AMBER"]:
        css_class = "risk-badge-warning"
    else:
        css_class = "risk-badge-healthy"
    
    return f'<span class="risk-badge {css_class}">{clean_level}</span>'

def render_data_label(tag: str):
    """Render observed / calculated / simulated / assumption badge."""
    clean_tag = str(tag).lower()
    return f'<span class="data-label">{clean_tag}</span>'

def render_alert_item(severity: str, title: str, message: str, entity_id: str = None, timestamp: str = None):
    """Render an alert card with semantic color border."""
    sev = str(severity).lower()
    if sev in ["critical", "high risk"]:
        cls = "alert-card-critical"
    elif sev == "high":
        cls = "alert-card-high"
    elif sev in ["warning", "medium"]:
        cls = "alert-card-warning"
    else:
        cls = "alert-card-healthy"
    
    meta_parts = []
    if entity_id:
        meta_parts.append(f'<span class="code-id">{entity_id}</span>')
    if timestamp:
        meta_parts.append(f'<span style="color: #9C9A96; font-size: 0.8rem;">{timestamp}</span>')
    meta_html = " &nbsp;•&nbsp; ".join(meta_parts)

    st.markdown(f"""
    <div class="alert-card {cls}">
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px;">
            <strong style="color: #F5F4F0; font-size: 0.95rem;">{title}</strong>
            {render_risk_badge(severity)}
        </div>
        <div style="color: #9C9A96; font-size: 0.85rem; margin-bottom: 6px;">{message}</div>
        <div>{meta_html}</div>
    </div>
    """, unsafe_allow_html=True)

def render_cascade_stepper(stages: list):
    """Render horizontal stage-by-stage cascade stepper."""
    cols = st.columns(len(stages))
    for i, (col, stage) in enumerate(zip(cols, stages)):
        with col:
            st.markdown(f"""
            <div class="terminal-card" style="text-align: center; border-top: 3px solid {COLOR_RISK_WARNING if stage.get('affected', 0) > 0 else '#3A3A3C'};">
                <div class="kpi-label">Stage {i+1}</div>
                <div style="font-weight: 600; font-size: 0.9rem; margin: 4px 0;">{stage.get('name', '')}</div>
                <div style="font-size: 1.25rem; font-weight: 700; color: #F5F4F0;">{stage.get('count', 0)}</div>
                <div style="font-size: 0.75rem; color: #9C9A96;">{stage.get('impact_text', '')}</div>
            </div>
            """, unsafe_allow_html=True)
