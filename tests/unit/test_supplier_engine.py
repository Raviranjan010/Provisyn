"""Unit tests for Supplier Intelligence engine (Phase 6)."""
import duckdb
import pandas as pd
from backend.data.repository import DuckDBRepository
from backend.data.generator import seed_database
from backend.engines.supplier import SupplierIntelligenceEngine

def test_supplier_profile_assembly_graceful_missing_data():
    """Verify profile assembly returns all required fields without KeyError even on empty database."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    # Database is completely empty, no tables exist
    engine = SupplierIntelligenceEngine(repo)

    profile = engine.get_supplier_profile("NON_EXISTENT_VENDOR")

    # Verify all expected keys are present
    required_keys = [
        "vendor_id", "name", "country_code", "city", "tier",
        "financial_health_score", "reliability_score", "delivery_performance",
        "capacity", "risk_score", "risk_category", "trend",
        "materials_supplied", "alternative_suppliers", "tier2_dependencies",
        "financial_exposure", "historical_disruptions"
    ]
    for k in required_keys:
        assert k in profile, f"Missing key '{k}' in supplier profile"

    assert profile["vendor_id"] == "NON_EXISTENT_VENDOR"
    assert profile["risk_category"] == "NOT_AVAILABLE"
    assert profile["financial_health_score"] is None
    assert profile["materials_supplied"] == []

def test_supplier_comparison_matrix():
    """Verify supplier comparison generates valid DataFrame for 2+ vendors."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    seed_database(repo, seed=42)

    engine = SupplierIntelligenceEngine(repo)
    vendors_df = repo.get_vendors()
    v_ids = vendors_df["VENDOR_ID"].head(3).tolist()

    comp_df = engine.compare_suppliers(v_ids)
    assert isinstance(comp_df, pd.DataFrame)
    assert len(comp_df) == 3
    assert "Supplier Name" in comp_df.columns
    assert "Risk Score" in comp_df.columns
    assert "Financial Health" in comp_df.columns
    assert "Alternates Available" in comp_df.columns
