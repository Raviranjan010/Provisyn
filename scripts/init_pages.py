import os

pages = [
    ('2_Risk_Intelligence.py', '02 RISK INTELLIGENCE', 'Risk Intelligence', 'Multi-tier risk quantification across 10 risk dimensions'),
    ('3_Network_Intelligence.py', '03 NETWORK INTELLIGENCE', 'Network Intelligence', 'Graph topology, PageRank centrality, and community clustering'),
    ('4_Hidden_Dependencies.py', '04 HIDDEN DEPENDENCIES', 'Hidden Dependencies', 'Uncover undisclosed Tier-2+ supply chain dependencies from trade flows'),
    ('5_Supplier_Intelligence.py', '05 SUPPLIER INTELLIGENCE', 'Supplier Intelligence', 'Supplier digital profiles, concentration metrics, and comparative evaluation'),
    ('6_Financial_Exposure.py', '06 FINANCIAL EXPOSURE', 'Financial Exposure', 'Quantify revenue-at-risk, production losses, and mitigation costs'),
    ('7_Demand_and_Inventory.py', '07 DEMAND & INVENTORY', 'Demand & Inventory', 'Risk-aware safety stock, days of cover, and stockout probability forecasting'),
    ('8_Resilience_Lab.py', '08 RESILIENCE LAB', 'Resilience Lab', 'Digital twin scenario simulation and Monte Carlo risk propagation'),
    ('9_Recommendations.py', '09 RECOMMENDATIONS', 'Recommendations', 'Optimization-ranked prescriptive mitigation actions and interventions'),
    ('10_PROVISYN_Copilot.py', '10 PROVISYN COPILOT', 'PROVISYN Copilot', 'Tool-grounded decision intelligence conversational assistant'),
    ('11_Model_Intelligence.py', '11 MODEL INTELLIGENCE', 'Model Intelligence', 'Model registry, performance metrics, PR-AUC curves, and drift tracking'),
    ('12_Alerts_and_Events.py', '12 ALERTS & EVENTS', 'Alerts & Events', 'Persisted operational event feed, threshold triggers, and predictive alerts'),
    ('13_Reports.py', '13 REPORTS', 'Reports', 'Auditable executive briefings and resilience audit exports'),
    ('14_About.py', '14 ABOUT', 'About', 'System architecture, methodology, author credentials, and foundation attribution')
]

template = '''"""PROVISYN — {title}"""
import sys
from pathlib import Path
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components.styles import inject_provisyn_styles
from frontend.utils.sidebar import render_sidebar

st.set_page_config(page_title="PROVISYN — {title}", layout="wide")
inject_provisyn_styles(st)
render_sidebar(current_page="{nav_name}")

st.markdown("""
<div style="border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem; margin-bottom: 1.5rem;">
    <h1 style="margin: 0; font-size: 1.75rem;">{heading}</h1>
    <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">{desc}</div>
</div>
""", unsafe_allow_html=True)

st.info("{nav_name} engine ready.")
'''

for fname, heading, nav_name, desc in pages:
    path = os.path.join('frontend', 'pages', fname)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(template.format(title=nav_name, heading=heading, nav_name=nav_name, desc=desc))
print('Created 13 page templates successfully.')
