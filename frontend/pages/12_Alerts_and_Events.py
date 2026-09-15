"""PROVISYN — Alerts & Events (Page 12).
Real-time operational alerts, predictive disruption warnings, and event management.
Persisted in the ALERTS repository table with genuine state management (ACTIVE / ACKNOWLEDGED / RESOLVED).
"""
import sys
from pathlib import Path
from datetime import datetime
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
    COLOR_RISK_HIGH,
    COLOR_RISK_CRITICAL,
)
from frontend.components import render_kpi, render_alert_item, render_risk_badge, render_data_label
from frontend.utils.sidebar import render_sidebar
from backend.data.repository import get_repository
from backend.data.generator import seed_database
from backend.engines.risk import RiskEngine
from backend.engines.spof import SPOFEngine
from backend.engines.inventory import InventoryEngine

st.set_page_config(page_title="PROVISYN — Alerts & Events", layout="wide")
inject_provisyn_styles(st)
render_sidebar(current_page="Alerts & Events")

# Header Strip
st.markdown("""
<div style="border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: baseline;">
    <div>
        <h1 style="margin: 0; font-size: 1.75rem;">12 ALERTS & INCIDENT EVENTS</h1>
        <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">Audited event bus, operational thresholds, predictive early warnings, and triage workflows</div>
    </div>
    <div>
        <span class="data-label">STATE: PERSISTENT REPOSITORY</span>
    </div>
</div>
""", unsafe_allow_html=True)

repo = get_repository()
vendors_df = repo.get_vendors()
if vendors_df.empty:
    seed_database(repo, seed=42)

alerts_df = repo.get_alerts()

# If empty, populate real alerts from engine findings
if alerts_df.empty:
    risk_engine = RiskEngine(repo)
    spof_engine = SPOFEngine(repo)
    inv_engine = InventoryEngine(repo)

    risk_df = risk_engine.compute_risk_scores()
    spof_df = spof_engine.identify_bottlenecks()
    inv_df = inv_engine.evaluate_inventory_portfolio()

    generated_alerts = []
    now = datetime.now()

    # 1. Critical SPOFs
    if not spof_df.empty:
        sev_col = "SEVERITY_TIER" if "SEVERITY_TIER" in spof_df.columns else ("SEVERITY" if "SEVERITY" in spof_df.columns else None)
        crit_spofs = spof_df[spof_df[sev_col] == "CRITICAL"] if sev_col else spof_df.head(2)
        for _, b in crit_spofs.iterrows():
            generated_alerts.append({
                "ALERT_ID": f"ALT-SPOF-{b['ENTITY_ID']}",
                "SEVERITY": "CRITICAL",
                "TRIGGER_TYPE": "SPOF_DISCOVERY",
                "ENTITY_TYPE": b.get("ENTITY_TYPE", "VENDOR"),
                "ENTITY_ID": str(b["ENTITY_ID"]),
                "MESSAGE": f"Single point of failure: zero redundant suppliers and high downstream blast radius identified for {b.get('ENTITY_NAME', b['ENTITY_ID'])}.",
                "IS_PREDICTIVE": False,
                "STATUS": "ACTIVE",
                "CREATED_AT": now
            })

    # 2. Critical Inventory Stockouts
    if not inv_df.empty:
        for _, item in inv_df[inv_df["STOCKOUT_RISK_LEVEL"] == "CRITICAL"].iterrows():
            generated_alerts.append({
                "ALERT_ID": f"ALT-INV-{item['MATERIAL_ID']}",
                "SEVERITY": "WARNING",
                "TRIGGER_TYPE": "STOCKOUT_RISK",
                "ENTITY_TYPE": "MATERIAL",
                "ENTITY_ID": str(item["MATERIAL_ID"]),
                "MESSAGE": f"{item['DESCRIPTION']} days of cover ({item['DAYS_OF_COVER']}d) is below dynamic safety threshold ({item['RISK_AWARE_SAFETY_STOCK']} units).",
                "IS_PREDICTIVE": True,
                "STATUS": "ACTIVE",
                "CREATED_AT": now
            })

    # 3. High Risk Vendors
    if not risk_df.empty:
        for _, r in risk_df[risk_df["RISK_SCORE"] >= 0.70].iterrows():
            generated_alerts.append({
                "ALERT_ID": f"ALT-RISK-{r['ENTITY_ID']}",
                "SEVERITY": "HIGH",
                "TRIGGER_TYPE": "THRESHOLD_BREACH",
                "ENTITY_TYPE": r["ENTITY_TYPE"],
                "ENTITY_ID": str(r["ENTITY_ID"]),
                "MESSAGE": f"High risk index ({r['RISK_SCORE']:.2f}) evaluated for {r.get('NAME', r['ENTITY_ID'])} exceeding 0.70 threshold.",
                "IS_PREDICTIVE": False,
                "STATUS": "ACTIVE",
                "CREATED_AT": now
            })

    if generated_alerts:
        alerts_df = pd.DataFrame(generated_alerts)
        repo.write_table(alerts_df, "ALERTS", overwrite=True)

# Metrics Strip
total_alerts = len(alerts_df)
crit_alerts = len(alerts_df[alerts_df.get("SEVERITY", "") == "CRITICAL"])
high_alerts = len(alerts_df[alerts_df.get("SEVERITY", "").isin(["HIGH", "WARNING"])])
active_alerts = len(alerts_df[alerts_df.get("STATUS", "") == "ACTIVE"])

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    render_kpi("Total Alerts", str(total_alerts), subtext="Recorded in database", data_label="observed")
with k2:
    render_kpi("Critical Severity", str(crit_alerts), subtext="Immediate triage needed", data_label="calculated")
with k3:
    render_kpi("Warning / High", str(high_alerts), subtext="Elevated operational risk", data_label="calculated")
with k4:
    render_kpi("Active Untriaged", str(active_alerts), subtext="Awaiting response", data_label="observed")
with k5:
    res_count = total_alerts - active_alerts
    render_kpi("Resolved / Ack", str(res_count), subtext="Mitigated incidents", data_label="audit")

st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

# Filter Controls
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    filter_sev = st.selectbox("Filter Severity", options=["ALL", "CRITICAL", "HIGH", "WARNING", "INFO"])
with col_f2:
    filter_status = st.selectbox("Filter Status", options=["ALL", "ACTIVE", "ACKNOWLEDGED", "RESOLVED"])
with col_f3:
    filter_type = st.selectbox("Filter Entity Type", options=["ALL", "VENDOR", "MATERIAL", "REGION"])

filtered_alerts = alerts_df.copy()
if filter_sev != "ALL":
    filtered_alerts = filtered_alerts[filtered_alerts["SEVERITY"] == filter_sev]
if filter_status != "ALL":
    filtered_alerts = filtered_alerts[filtered_alerts["STATUS"] == filter_status]
if filter_type != "ALL":
    filtered_alerts = filtered_alerts[filtered_alerts["ENTITY_TYPE"] == filter_type]

# Alert Feed & Triage Actions
col_feed, col_triage = st.columns([3, 2])

with col_feed:
    st.markdown("### Active Incident & Warning Feed")
    if filtered_alerts.empty:
        st.info("No alerts matching current filter parameters.")
    else:
        for idx, alt in filtered_alerts.iterrows():
            aid = str(alt.get("ALERT_ID", ""))
            sev = str(alt.get("SEVERITY", "WARNING"))
            status = str(alt.get("STATUS", "ACTIVE"))
            ts = str(alt.get("CREATED_AT", ""))[:16]
            is_pred = bool(alt.get("IS_PREDICTIVE", False))
            pred_tag = " [PREDICTIVE]" if is_pred else ""

            render_alert_item(
                severity=sev,
                title=f"{alt.get('TRIGGER_TYPE', 'ALERT').replace('_', ' ')}{pred_tag} ({status})",
                message=str(alt.get("MESSAGE", "")),
                entity_id=f"{alt.get('ENTITY_TYPE', '')}:{alt.get('ENTITY_ID', '')}",
                timestamp=ts
            )

with col_triage:
    st.markdown("### Incident Action & Triage")
    if not filtered_alerts.empty:
        target_alert_id = st.selectbox(
            "Select Alert to Triage",
            options=filtered_alerts["ALERT_ID"].tolist()
        )
        selected_row = filtered_alerts[filtered_alerts["ALERT_ID"] == target_alert_id].iloc[0]

        st.markdown(f"""
        <div class="terminal-card" style="margin-bottom: 1rem;">
            <div><b>Alert:</b> <code class="code-id">{target_alert_id}</code></div>
            <div><b>Entity:</b> {selected_row.get('ENTITY_TYPE')}:{selected_row.get('ENTITY_ID')}</div>
            <div><b>Current Status:</b> <span class="data-label">{selected_row.get('STATUS')}</span></div>
            <div style="margin-top: 6px; font-size: 0.85rem; color: #9C9A96;">{selected_row.get('MESSAGE')}</div>
        </div>
        """, unsafe_allow_html=True)

        c_act1, c_act2 = st.columns(2)
        with c_act1:
            if st.button("Acknowledge Alert", use_container_width=True):
                alerts_df.loc[alerts_df["ALERT_ID"] == target_alert_id, "STATUS"] = "ACKNOWLEDGED"
                repo.write_table(alerts_df, "ALERTS", overwrite=True)
                st.success(f"Alert {target_alert_id} acknowledged.")
                st.rerun()
        with c_act2:
            if st.button("Resolve Alert", type="primary", use_container_width=True):
                alerts_df.loc[alerts_df["ALERT_ID"] == target_alert_id, "STATUS"] = "RESOLVED"
                repo.write_table(alerts_df, "ALERTS", overwrite=True)
                st.success(f"Alert {target_alert_id} marked as resolved.")
                st.rerun()

    # Manual Alert Creation Form
    st.markdown("#### Broadcast Operational Incident")
    with st.form("manual_alert_form"):
        new_sev = st.selectbox("Severity", ["CRITICAL", "HIGH", "WARNING", "INFO"])
        new_trigger = st.selectbox("Trigger Type", ["GEOPOLITICAL_DISRUPTION", "PORT_STRIKE", "SUPPLIER_INSOLVENCY", "WEATHER_EVENT"])
        new_etype = st.selectbox("Entity Type", ["VENDOR", "MATERIAL", "REGION"])
        new_eid = st.text_input("Entity ID", value="V10001")
        new_msg = st.text_area("Alert Description", value="Sudden operational shutdown reported at processing terminal.")
        submitted = st.form_submit_button("Broadcast Alert to Network")
        if submitted:
            new_record = {
                "ALERT_ID": f"ALT-MAN-{datetime.now().strftime('%H%M%S')}",
                "SEVERITY": new_sev,
                "TRIGGER_TYPE": new_trigger,
                "ENTITY_TYPE": new_etype,
                "ENTITY_ID": new_eid,
                "MESSAGE": new_msg,
                "IS_PREDICTIVE": False,
                "STATUS": "ACTIVE",
                "CREATED_AT": datetime.now()
            }
            updated_df = pd.concat([alerts_df, pd.DataFrame([new_record])], ignore_index=True)
            repo.write_table(updated_df, "ALERTS", overwrite=True)
            st.success("New operational alert broadcasted and persisted.")
            st.rerun()
