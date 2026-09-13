"""Unit tests for Inventory Intelligence Engine (Phase 11)."""
import math
import duckdb
from backend.data.repository import DuckDBRepository
from backend.data.generator import seed_database
from backend.engines.inventory import InventoryEngine

def test_inventory_formulas_hand_computed_examples():
    """Verify Days of Cover, Reorder Point, and Risk-Aware Safety Stock against hand-computed values.
    Example:
      On-Hand = 600 units
      Daily Demand = 20 units/day -> Days of Cover = 600 / 20 = 30.0 days
      Lead Time = 14 days
      Base Safety Stock = 200 units
      Supplier Risk Score = 0.80
      Risk Multiplier = 0.50 -> Scaled Safety Stock = 200 * (1 + 0.80 * 0.50) = 200 * 1.40 = 280.0 units
      Reorder Point = (20 * 14) + 280.0 = 280 + 280 = 560.0 units
    """
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    engine = InventoryEngine(repo)

    doc = engine.calculate_days_of_cover(on_hand=600.0, daily_demand=20.0)
    assert abs(doc - 30.0) < 1e-5

    safety = engine.calculate_risk_aware_safety_stock(base_safety_stock=200.0, risk_score=0.80)
    assert abs(safety - 280.0) < 1e-5

    rop = engine.calculate_reorder_point(daily_demand=20.0, lead_time_days=14, safety_stock=safety)
    assert abs(rop - 560.0) < 1e-5

def test_extremely_high_demand_does_not_overflow_or_nan():
    """Verify extreme inputs (e.g. infinite demand surge) return valid bounded probabilities [0.0, 1.0]."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    engine = InventoryEngine(repo)

    # 1. Extremely high demand (days of cover near 0, growth 1000%)
    prob_high = engine.predict_stockout_probability(
        days_of_cover=0.01,
        lead_time_days=90,
        supplier_risk_score=1.0,
        demand_growth_rate=100.0
    )
    assert not math.isnan(prob_high)
    assert not math.isinf(prob_high)
    assert 0.0 <= prob_high <= 1.0
    assert prob_high > 0.90  # Extremely high risk

    # 2. Extremely high buffer (days of cover = 1000 days)
    prob_low = engine.predict_stockout_probability(
        days_of_cover=1000.0,
        lead_time_days=10,
        supplier_risk_score=0.0,
        demand_growth_rate=0.0
    )
    assert not math.isnan(prob_low)
    assert 0.0 <= prob_low <= 0.05  # Negligible risk
