"""Test suite to validate UI styling constraints per design.md (Phase 4)."""
import os
import re
from pathlib import Path
from frontend.components.styles import GLOBAL_CSS
from frontend.utils.sidebar import PAGES

def test_no_gradients_in_css():
    """Verify that no linear or radial gradients exist anywhere in the CSS."""
    assert "gradient" not in GLOBAL_CSS.lower()
    assert "linear-gradient" not in GLOBAL_CSS.lower()
    assert "radial-gradient" not in GLOBAL_CSS.lower()

def test_no_blue_status_or_primary_color():
    """Verify that blue colors (e.g. #3b82f6 or similar) are retired and not present in CSS."""
    blue_hex_patterns = [
        r"#3b82f6", r"#2563eb", r"#1d4ed8", r"#60a5fa", r"#93c5fd",
        r"#0000ff", r"#0284c7", r"#0ea5e9", r"#38bdf8"
    ]
    for pattern in blue_hex_patterns:
        match = re.search(pattern, GLOBAL_CSS, re.IGNORECASE)
        assert match is None, f"Found forbidden blue color {pattern} in GLOBAL_CSS"

def test_no_glassmorphism_blur_in_css():
    """Verify that backdrop-filter glassmorphism is not used."""
    assert "backdrop-filter" not in GLOBAL_CSS.lower()

def test_all_14_pages_in_navigation():
    """Verify that the sidebar defines exactly the 14-item Part 11 IA."""
    assert len(PAGES) == 14
    expected_names = [
        "Command Overview", "Risk Intelligence", "Network Intelligence",
        "Hidden Dependencies", "Supplier Intelligence", "Financial Exposure",
        "Demand & Inventory", "Resilience Lab", "Recommendations",
        "PROVISYN Copilot", "Model Intelligence", "Alerts & Events",
        "Reports", "About"
    ]
    actual_names = [p["name"] for p in PAGES]
    assert actual_names == expected_names

def test_page_files_exist():
    """Verify that all 14 page files exist on disk."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    app_root = root_dir / "frontend" / "streamlit_app.py"
    assert app_root.exists(), "frontend/streamlit_app.py must exist"
    
    for p in PAGES[1:]:  # skip command overview which is streamlit_app.py
        p_path = root_dir / "frontend" / p["path"]
        assert p_path.exists(), f"Page file {p_path} must exist"
