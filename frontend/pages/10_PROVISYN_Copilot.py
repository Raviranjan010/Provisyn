"""PROVISYN — PROVISYN Copilot (Page 10).
Tool-grounded conversational decision assistant.
Strictly verifies that every numeric claim traces directly to an analytical engine tool invocation.
Displays tool citations with monospace identifier formatting and explicit source tags.
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
from frontend.components import render_data_label, render_risk_badge
from frontend.utils.sidebar import render_sidebar
from backend.data.repository import get_repository
from backend.data.generator import seed_database
from backend.copilot.agent import CopilotAgent

st.set_page_config(page_title="PROVISYN — Copilot", layout="wide")
inject_provisyn_styles(st)
render_sidebar(current_page="PROVISYN Copilot")

# Header Strip
st.markdown("""
<div style="border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: baseline;">
    <div>
        <h1 style="margin: 0; font-size: 1.75rem;">10 PROVISYN COPILOT</h1>
        <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">Tool-grounded decision intelligence agent with strict mathematical attribution and auditability</div>
    </div>
    <div>
        <span class="data-label">AGENT ENGINE: TOOL GROUNDED</span>
        <span class="data-label">VERIFICATION: ZERO HALLUCINATION</span>
    </div>
</div>
""", unsafe_allow_html=True)

repo = get_repository()
vendors_df = repo.get_vendors()
if vendors_df.empty:
    seed_database(repo, seed=42)

# Initialize Copilot Agent
if "copilot_agent" not in st.session_state:
    st.session_state["copilot_agent"] = CopilotAgent(repo)

agent: CopilotAgent = st.session_state["copilot_agent"]

# Initialize Chat History
if "copilot_messages" not in st.session_state:
    st.session_state["copilot_messages"] = [
        {
            "role": "assistant",
            "content": "Hello. I am the **PROVISYN Decision Copilot**. All of my assessments, risk metrics, financial estimates, and recommendations are directly computed from analytical engine tool invocations. How may I assist your supply chain operations today?",
            "facts": [],
            "tool": None,
            "timestamp": "Session Start"
        }
    ]

# Layout: Chat Column + Tool Registry Side Panel
chat_col, panel_col = st.columns([3, 1])

with panel_col:
    st.markdown("### Grounded Tools")
    st.markdown("""
    <div class="terminal-card" style="font-size: 0.82rem; line-height: 1.5; margin-bottom: 1rem;">
        <div><b>Active Engine Tools:</b></div>
        <div style="margin-top: 6px;">• <code class="code-id">risk_engine</code>: Multi-tier SHAP score query</div>
        <div>• <code class="code-id">graph_engine</code>: SPOF & centrality detection</div>
        <div>• <code class="code-id">financial_engine</code>: Exposure & revenue-at-risk</div>
        <div>• <code class="code-id">simulation_engine</code>: Monte Carlo stress-testing</div>
        <div>• <code class="code-id">optimization_engine</code>: PuLP knapsack actions</div>
        <div>• <code class="code-id">inventory_engine</code>: Dynamic safety stock buffers</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Query Prompts")
    prompt_pills = [
        "Why is Outback Lithium high risk?",
        "Identify top supply chain single points of failure",
        "Calculate financial exposure for Outback Lithium",
        "Recommend mitigations for $500k budget",
        "Simulate Australian lithium port disruption for 45 days"
    ]
    
    selected_quick_prompt = None
    for p in prompt_pills:
        if st.button(p, key=f"btn_p_{hash(p)}", use_container_width=True):
            selected_quick_prompt = p

with chat_col:
    # Render Chat History
    for msg in st.session_state["copilot_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # If facts are returned from engine tool, render them with monospace / source styling
            if msg.get("facts"):
                facts_html = []
                for f in msg["facts"]:
                    facts_html.append(
                        f"""<div style="display: inline-block; background: #2B2B2E; border: 1px solid #3A3A3C; border-radius: 4px; padding: 4px 8px; margin: 3px; font-size: 0.8rem;">
                            <span style="color: #9C9A96;">{f['label']}:</span> <code class="code-id">{f['value']}</code>
                            <span class="data-label" style="margin-left: 6px;">source: {f['source']}</span>
                        </div>"""
                    )
                st.markdown("<div style='margin-top: 8px;'>" + "".join(facts_html) + "</div>", unsafe_allow_html=True)

    # Handle User Input
    user_query = st.chat_input("Inquire about suppliers, materials, bottlenecks, or simulations...") or selected_quick_prompt

    if user_query:
        # Append User Message
        st.session_state["copilot_messages"].append({
            "role": "user",
            "content": user_query,
            "facts": [],
            "tool": None,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

        # Process Query with Agent
        response_dict = agent.process_query(user_query)

        # Append Assistant Response
        st.session_state["copilot_messages"].append({
            "role": "assistant",
            "content": response_dict.get("narrative", "Query processed."),
            "facts": response_dict.get("facts", []),
            "tool": response_dict.get("tool_name"),
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

        st.rerun()
