"""PROVISYN — Supplier Intelligence (Page 5).
360-degree Supplier Digital Profiles, concentration metrics, and multi-supplier comparative evaluation.
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
from frontend.components import render_kpi, render_risk_badge
from frontend.utils.sidebar import render_sidebar
from backend.data.repository import get_repository
from backend.data.generator import seed_database
from backend.engines.supplier import SupplierIntelligenceEngine
from backend.engines.risk import RiskEngine

st.set_page_config(page_title="PROVISYN — Supplier Intelligence", layout="wide")
inject_provisyn_styles(st)
render_sidebar(current_page="Supplier Intelligence")

st.markdown("""
<div style="border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: baseline;">
    <div>
        <h1 style="margin: 0; font-size: 1.75rem;">05 SUPPLIER INTELLIGENCE</h1>
        <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">Comprehensive 360° digital supplier profiles, multi-tier dependency mapping, and comparative benchmarking</div>
    </div>
    <div>
        <span class="data-label">PROFILE AGGREGATION ENGINE</span>
    </div>
</div>
""", unsafe_allow_html=True)

repo = get_repository()
vendors_df = repo.get_vendors()
if vendors_df.empty:
    seed_database(repo, seed=42)
    vendors_df = repo.get_vendors()

# Ensure risk scores computed
risk_df = repo.get_risk_scores()
if risk_df.empty:
    risk_engine = RiskEngine(repo)
    risk_df = risk_engine.compute_risk_scores()

supplier_engine = SupplierIntelligenceEngine(repo)

tab_profile, tab_compare = st.tabs(["Supplier Digital Profile", "Multi-Supplier Comparison"])

with tab_profile:
    vendor_options = vendors_df.sort_values("NAME")["VENDOR_ID"].tolist()
    vendor_name_map = {row["VENDOR_ID"]: f"{row['NAME']} ({row['VENDOR_ID']}) - {row['COUNTRY_CODE']}" for _, row in vendors_df.iterrows()}
    
    col_sel, col_empty = st.columns([3, 2])
    with col_sel:
        selected_vid = st.selectbox(
            "Select Supplier to Inspect",
            options=vendor_options,
            format_func=lambda vid: vendor_name_map.get(vid, vid)
        )
    
    profile = supplier_engine.get_supplier_profile(selected_vid)
    
    # KPI Strip for Supplier
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        risk_val = f"{profile['risk_score']:.3f}" if profile['risk_score'] is not None else "N/A"
        render_kpi("Supplier Risk Score", risk_val, subtext=profile["risk_category"], data_label="calculated")
    with k2:
        fh_val = f"{profile['financial_health_score'] * 100:.0f}%" if profile['financial_health_score'] is not None else "N/A"
        render_kpi("Financial Health", fh_val, subtext="Solvency & working capital", data_label="observed")
    with k3:
        otif_val = f"{profile['delivery_performance'] * 100:.0f}%" if profile['delivery_performance'] is not None else "N/A"
        render_kpi("Delivery OTIF", otif_val, subtext=f"Reliability: {profile['reliability_score'] * 100:.0f}%" if profile['reliability_score'] else "", data_label="observed")
    with k4:
        render_kpi("Attributable Exposure", f"${profile['financial_exposure']/1e3:,.1f}K", subtext="Direct downstream risk", data_label="calculated")

    st.markdown("""<div style="margin-top: 1rem;"></div>""", unsafe_allow_html=True)

    c_left, c_right = st.columns([1, 1])
    
    with c_left:
        st.markdown("### Profile Metadata & Operations")
        st.markdown(f"""
        <div class="terminal-card">
            <div style="font-size: 1.15rem; font-weight: 700; margin-bottom: 8px;">{profile['name']}</div>
            <div style="color: #9C9A96; font-size: 0.85rem; line-height: 1.6;">
                <strong>ID:</strong> <span class="code-id">{profile['vendor_id']}</span> &nbsp;•&nbsp; 
                <strong>Country:</strong> {profile['country_code']} &nbsp;•&nbsp; 
                <strong>City:</strong> {profile['city']}<br>
                <strong>Tier:</strong> Tier-{profile['tier']} Supplier &nbsp;•&nbsp; 
                <strong>Capacity:</strong> {profile['capacity']:,.0f} units/month<br>
                <strong>Phone:</strong> {profile['phone']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### Materials Supplied")
        if profile["materials_supplied"]:
            mat_rows = [{"Material ID": m["material_id"], "Description": m["description"]} for m in profile["materials_supplied"]]
            st.dataframe(pd.DataFrame(mat_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No materials actively contracted.")

    with c_right:
        st.markdown("### Upstream Tier-2 Dependencies")
        if profile["tier2_dependencies"]:
            for d in profile["tier2_dependencies"]:
                st.markdown(f"""
                <div class="terminal-card" style="border-left: 3px solid {COLOR_RISK_CRITICAL};">
                    <div style="font-weight: 600; font-size: 0.95rem;">{d['shipper_name']}</div>
                    <div style="color: #9C9A96; font-size: 0.8rem; margin-top: 4px;">
                        Trade Inferred Connection • Similarity: <strong>{d['similarity']:.3f}</strong> • Confidence: <strong>{d['confidence']*100:.0f}%</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="terminal-card">
                <div style="color: #9C9A96; font-size: 0.85rem;">
                    No hidden Tier-2 trade-flow bottlenecks identified for this supplier in the trade bill of lading data.
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("#### Identified Alternate Suppliers")
        if profile["alternative_suppliers"]:
            st.markdown(f"Found **{len(profile['alternative_suppliers'])}** alternate vendors in network supplying overlapping materials:")
            st.markdown(", ".join([f"<span class='code-id'>{vid}</span>" for vid in profile["alternative_suppliers"]]), unsafe_allow_html=True)
        else:
            st.warning("Sole source alert: No alternative vendors in the active graph currently supply these exact materials.")

with tab_compare:
    st.markdown("### Benchmark Multiple Suppliers Side-by-Side")
    default_selection = vendor_options[:3] if len(vendor_options) >= 3 else vendor_options
    selected_vendors = st.multiselect(
        "Select Suppliers to Compare (min 2)",
        options=vendor_options,
        default=default_selection,
        format_func=lambda vid: vendor_name_map.get(vid, vid)
    )
    
    if len(selected_vendors) >= 2:
        comp_df = supplier_engine.compare_suppliers(selected_vendors)
        st.dataframe(comp_df, use_container_width=True, hide_index=True)
    else:
        st.info("Please select at least 2 suppliers to render comparative benchmarking.")
