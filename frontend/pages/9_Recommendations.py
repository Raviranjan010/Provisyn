"""PROVISYN — Recommendations"""
import sys
from pathlib import Path
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components.styles import inject_provisyn_styles
from frontend.utils.sidebar import render_sidebar

st.set_page_config(page_title="PROVISYN — Recommendations", layout="wide")
inject_provisyn_styles(st)
render_sidebar(current_page="Recommendations")

st.markdown("""
<div style="border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem; margin-bottom: 1.5rem;">
    <h1 style="margin: 0; font-size: 1.75rem;">09 RECOMMENDATIONS</h1>
    <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">Optimization-ranked prescriptive mitigation actions and interventions</div>
</div>
""", unsafe_allow_html=True)

st.info("Recommendations engine ready.")
