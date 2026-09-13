"""PROVISYN — Alerts & Events"""
import sys
from pathlib import Path
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components.styles import inject_provisyn_styles
from frontend.utils.sidebar import render_sidebar

st.set_page_config(page_title="PROVISYN — Alerts & Events", layout="wide")
inject_provisyn_styles(st)
render_sidebar(current_page="Alerts & Events")

st.markdown("""
<div style="border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem; margin-bottom: 1.5rem;">
    <h1 style="margin: 0; font-size: 1.75rem;">12 ALERTS & EVENTS</h1>
    <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">Persisted operational event feed, threshold triggers, and predictive alerts</div>
</div>
""", unsafe_allow_html=True)

st.info("Alerts & Events engine ready.")
