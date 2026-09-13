"""Unit tests for Cascade Risk Propagation Engine (Phase 9)."""
import duckdb
from backend.data.repository import DuckDBRepository
from backend.data.generator import seed_database
from backend.engines.cascade import CascadeEngine

def test_cascade_single_supplier_and_disconnected_cases():
    """Verify that disconnected graphs and single-supplier edge cases do not crash."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    seed_database(repo, seed=42)

    engine = CascadeEngine(repo)

    # Disconnected / non-existent entity
    result_none = engine.simulate_disruption(seed_entities=["NON_EXISTENT_VENDOR"])
    assert result_none.revenue_at_risk == 0.0
    assert len(result_none.affected_suppliers) == 0

    # Single supplier
    result_single = engine.simulate_disruption(seed_entities=["V10001"])
    assert len(result_single.stages) == 7
    assert len(result_single.affected_suppliers) == 1
    assert result_single.revenue_at_risk >= 0.0

def test_simultaneous_multi_supplier_failure_is_superset():
    """Verify simultaneous multi-supplier failure produces a superset of single-failure impact."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    seed_database(repo, seed=42)

    engine = CascadeEngine(repo)

    res1 = engine.simulate_disruption(seed_entities=["V10001"])
    res2 = engine.simulate_disruption(seed_entities=["V10002"])
    res_both = engine.simulate_disruption(seed_entities=["V10001", "V10002"])

    # Multi-failure affected suppliers should contain both
    assert set(res1.affected_suppliers).issubset(set(res_both.affected_suppliers))
    assert set(res2.affected_suppliers).issubset(set(res_both.affected_suppliers))
    assert len(res_both.affected_suppliers) >= len(res1.affected_suppliers)
    assert set(res1.affected_materials).issubset(set(res_both.affected_materials))

def test_cascade_stopping_depth():
    """Verify traversal stops at documented stopping condition max_depth."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    seed_database(repo, seed=42)

    engine = CascadeEngine(repo)
    # Depth 0 stops BOM expansion
    res_shallow = engine.simulate_disruption(seed_entities=["V10001"], max_depth=0)
    res_deep = engine.simulate_disruption(seed_entities=["V10001"], max_depth=10)

    assert len(res_shallow.affected_materials) <= len(res_deep.affected_materials)
