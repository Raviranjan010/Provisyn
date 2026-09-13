"""Unit tests for Financial Exposure Engine (Phase 10)."""
import duckdb
import pandas as pd
from backend.data.repository import DuckDBRepository
from backend.data.generator import seed_database
from backend.engines.financial import FinancialExposureEngine

def test_financial_exposure_zero_revenue_and_zero_inventory_edge_cases():
    """Verify zero-revenue and zero-inventory edge cases return 0.0 with proper labels, not exceptions."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    
    # Create empty database with no orders and no inventory
    engine = FinancialExposureEngine(repo)
    result = engine.calculate_exposure(seed_entities=["V10001"])

    assert result.revenue_at_risk == 0.0
    assert result.holding_cost == 0.0
    assert result.production_loss == 0.0
    assert result.total_financial_exposure == 0.0
    assert result.expected_loss == 0.0

    # Ensure all labels exist
    assert "revenue_at_risk" in result.labels
    assert "expediting_cost" in result.labels
    assert result.labels["expediting_cost"] == "assumption"

def test_financial_exposure_labels_convention():
    """Verify all financial outputs carry an explicit observed/calculated/simulated/assumption label."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    seed_database(repo, seed=42)

    po = repo.get_purchase_orders()
    test_vendor = po["VENDOR_ID"].iloc[0]

    engine = FinancialExposureEngine(repo)
    result = engine.calculate_exposure(seed_entities=[test_vendor], shock_severity=0.8, disruption_probability=0.3)

    assert result.total_financial_exposure > 0.0
    assert result.expected_loss > 0.0

    allowed_labels = {"observed", "calculated", "simulated", "assumption"}
    for metric, label in result.labels.items():
        assert label in allowed_labels, f"Metric '{metric}' has invalid label '{label}'"
