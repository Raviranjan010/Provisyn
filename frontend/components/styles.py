"""PROVISYN Design System — Industrial Terminal Theme.
Strict adherence to design.md:
- No gradients.
- No glassmorphism.
- No blue as primary or status color.
- Flat charcoal (#1C1C1E, #242426, #2B2B2E) and off-white (#F5F4F0) palette.
- Semantic risk colors: Healthy (#5B8266), Warning (#C99A3B), High (#C97A3B), Critical (#B14A3E).
- 4px consistent border radius.
- Tabular figures.
"""

# Semantic Color Constants
COLOR_CANVAS = "#1C1C1E"
COLOR_SURFACE = "#242426"
COLOR_SURFACE_RAISED = "#2B2B2E"
COLOR_TEXT_PRIMARY = "#F5F4F0"
COLOR_TEXT_SECONDARY = "#9C9A96"
COLOR_BORDER = "#3A3A3C"
COLOR_ACCENT = "#5B7A63"

# Semantic Risk Colors (Zero Blue)
COLOR_RISK_HEALTHY = "#5B8266"    # Muted Green
COLOR_RISK_WARNING = "#C99A3B"    # Amber
COLOR_RISK_HIGH = "#C97A3B"       # Orange
COLOR_RISK_CRITICAL = "#B14A3E"   # Red

GLOBAL_CSS = f"""
<style>
    /* 1. Global Reset & Flat Charcoal Background */
    html, body, .stApp, [data-testid="stAppViewContainer"], .main, [data-testid="stMain"] {{
        background-color: {COLOR_CANVAS} !important;
        background-image: none !important;
        color: {COLOR_TEXT_PRIMARY} !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        font-variant-numeric: tabular-nums !important;
    }}

    /* 2. Flat Sidebar */
    [data-testid="stSidebar"], section[data-testid="stSidebar"] {{
        background-color: {COLOR_SURFACE} !important;
        background-image: none !important;
        border-right: 1px solid {COLOR_BORDER} !important;
    }}
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {{
        color: {COLOR_TEXT_PRIMARY} !important;
    }}

    /* 3. Typography & Headings */
    h1, h2, h3, h4, h5, h6 {{
        color: {COLOR_TEXT_PRIMARY} !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
    }}
    
    p, span, label, li {{
        color: {COLOR_TEXT_PRIMARY} !important;
    }}

    .sub-label {{
        color: {COLOR_TEXT_SECONDARY} !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }}

    /* 4. Terminal KPI Tile */
    .kpi-tile {{
        background-color: {COLOR_SURFACE} !important;
        border: 1px solid {COLOR_BORDER} !important;
        border-radius: 4px !important;
        padding: 1rem 1.25rem !important;
        margin-bottom: 0.75rem !important;
    }}
    .kpi-label {{
        font-size: 0.8rem !important;
        color: {COLOR_TEXT_SECONDARY} !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        margin-bottom: 0.35rem !important;
    }}
    .kpi-value {{
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        color: {COLOR_TEXT_PRIMARY} !important;
        font-variant-numeric: tabular-nums !important;
        line-height: 1.1 !important;
    }}
    .kpi-subtext {{
        font-size: 0.8rem !important;
        color: {COLOR_TEXT_SECONDARY} !important;
        margin-top: 0.35rem !important;
    }}

    /* 5. Flat Containers & Cards */
    .terminal-card {{
        background-color: {COLOR_SURFACE} !important;
        border: 1px solid {COLOR_BORDER} !important;
        border-radius: 4px !important;
        padding: 1.25rem !important;
        margin-bottom: 1rem !important;
    }}

    /* 6. Semantic Risk Badges */
    .risk-badge {{
        display: inline-block !important;
        padding: 2px 8px !important;
        border-radius: 4px !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
    }}
    .risk-badge-healthy {{
        background-color: {COLOR_RISK_HEALTHY}22 !important;
        color: {COLOR_RISK_HEALTHY} !important;
        border: 1px solid {COLOR_RISK_HEALTHY} !important;
    }}
    .risk-badge-warning {{
        background-color: {COLOR_RISK_WARNING}22 !important;
        color: {COLOR_RISK_WARNING} !important;
        border: 1px solid {COLOR_RISK_WARNING} !important;
    }}
    .risk-badge-high {{
        background-color: {COLOR_RISK_HIGH}22 !important;
        color: {COLOR_RISK_HIGH} !important;
        border: 1px solid {COLOR_RISK_HIGH} !important;
    }}
    .risk-badge-critical {{
        background-color: {COLOR_RISK_CRITICAL}22 !important;
        color: {COLOR_RISK_CRITICAL} !important;
        border: 1px solid {COLOR_RISK_CRITICAL} !important;
    }}

    /* 7. Data Label Badges */
    .data-label {{
        display: inline-block !important;
        font-family: monospace !important;
        font-size: 0.7rem !important;
        padding: 1px 6px !important;
        border-radius: 4px !important;
        border: 1px solid {COLOR_BORDER} !important;
        background-color: {COLOR_SURFACE_RAISED} !important;
        color: {COLOR_TEXT_SECONDARY} !important;
        margin-left: 6px !important;
    }}

    /* 8. Alert Items */
    .alert-card {{
        background-color: {COLOR_SURFACE} !important;
        border: 1px solid {COLOR_BORDER} !important;
        border-left: 4px solid {COLOR_BORDER} !important;
        border-radius: 0 4px 4px 0 !important;
        padding: 0.85rem 1rem !important;
        margin-bottom: 0.75rem !important;
    }}
    .alert-card-critical {{ border-left-color: {COLOR_RISK_CRITICAL} !important; }}
    .alert-card-high {{ border-left-color: {COLOR_RISK_HIGH} !important; }}
    .alert-card-warning {{ border-left-color: {COLOR_RISK_WARNING} !important; }}
    .alert-card-healthy {{ border-left-color: {COLOR_RISK_HEALTHY} !important; }}

    /* 9. Monospace Identifier styling */
    .code-id {{
        font-family: monospace !important;
        background-color: {COLOR_SURFACE_RAISED} !important;
        color: {COLOR_TEXT_PRIMARY} !important;
        padding: 2px 5px !important;
        border-radius: 4px !important;
        border: 1px solid {COLOR_BORDER} !important;
        font-size: 0.85em !important;
    }}

    /* 10. Tables & DataFrames */
    [data-testid="stDataFrame"] {{
        border: 1px solid {COLOR_BORDER} !important;
        border-radius: 4px !important;
    }}

    /* Hide default decoration */
    #MainMenu, footer, .stDeployButton {{ display: none !important; }}
    [data-testid="stSidebarNav"] {{ display: none !important; }}
</style>
"""

def inject_provisyn_styles(st_module):
    """Inject the core design system into the Streamlit page."""
    st_module.markdown(GLOBAL_CSS, unsafe_allow_html=True)
