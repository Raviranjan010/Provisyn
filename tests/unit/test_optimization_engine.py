"""Unit tests for Optimization Engine and PuLP constraint satisfaction (Phase 13)."""
import duckdb
from backend.data.repository import DuckDBRepository
from backend.engines.optimization import OptimizationEngine

def test_optimization_never_exceeds_budget():
    """Verify solver output never exceeds specified budget constraint."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    engine = OptimizationEngine(repo)

    budgets = [100000.0, 250000.0, 500000.0, 1000000.0]
    for b in budgets:
        res = engine.optimize_allocations(budget=b)
        assert res.is_feasible
        assert res.total_spend <= b, f"Total spend {res.total_spend} exceeded budget {b}"

def test_infeasible_budget_returns_unavailable():
    """Verify infeasible budget returns 'OPTIMIZATION_UNAVAILABLE' and not a fabricated ranking."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    engine = OptimizationEngine(repo)

    # Budget below lowest cost action ($65,000)
    res = engine.optimize_allocations(budget=1000.0)
    assert not res.is_feasible
    assert res.status == "OPTIMIZATION_UNAVAILABLE"
    assert len(res.selected_actions) == 0
    assert "unavailable" in res.message.lower()

def test_optimization_stability_run_twice():
    """Verify running optimization twice with identical inputs yields identical allocations."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    engine = OptimizationEngine(repo)

    res1 = engine.optimize_allocations(budget=400000.0)
    res2 = engine.optimize_allocations(budget=400000.0)

    assert res1.total_spend == res2.total_spend
    assert res1.total_exposure_reduction == res2.total_exposure_reduction
    act_ids_1 = [a["action_id"] for a in res1.selected_actions]
    act_ids_2 = [a["action_id"] for a in res2.selected_actions]
    assert act_ids_1 == act_ids_2
