"""Unit tests for Simulation Engine and Resilience Lab (Phase 12)."""
import duckdb
from backend.data.repository import DuckDBRepository
from backend.data.generator import seed_database
from backend.engines.simulation import SimulationEngine, SCENARIO_TYPES
from backend.engines.resilience import ResilienceEngine

def test_monte_carlo_p10_p50_p90_ordering():
    """Verify Monte Carlo simulation output strictly satisfies P10 <= P50 <= P90."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    seed_database(repo, seed=42)

    engine = SimulationEngine(repo)
    po = repo.get_purchase_orders()
    target_vendor = po["VENDOR_ID"].iloc[0]

    sim = engine.run_scenario(
        scenario_type="SUPPLIER_FAILURE",
        target_entities=[target_vendor],
        intensity=0.8,
        duration_days=30,
        n_iterations=150
    )

    assert sim.monte_carlo_p10 <= sim.monte_carlo_p50 <= sim.monte_carlo_p90
    assert sim.monte_carlo_p10 >= 0.0

def test_all_9_scenario_types_run_without_error():
    """Verify all 9 scenario types from Part 15 execute successfully on the seeded dataset."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    seed_database(repo, seed=42)

    engine = SimulationEngine(repo)
    po = repo.get_purchase_orders()
    target_vendor = po["VENDOR_ID"].iloc[0]

    for stype in SCENARIO_TYPES:
        target = ["AUS"] if "COUNTRY" in stype or "PORT" in stype else [target_vendor]
        res = engine.run_scenario(
            scenario_type=stype,
            target_entities=target,
            intensity=0.7,
            duration_days=25,
            n_iterations=20
        )
        assert res.scenario_type == stype
        assert res.monte_carlo_p10 <= res.monte_carlo_p50 <= res.monte_carlo_p90

def test_beneficial_intervention_increases_resilience_score():
    """Verify resilience score increases positively following beneficial interventions."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    res_engine = ResilienceEngine(repo)

    base = res_engine.calculate_resilience_score()
    base_score = base["resilience_score"]

    eval_result = res_engine.evaluate_intervention(
        baseline_score=base_score,
        intervention_type="REGIONAL_DUAL_SOURCING",
        investment_cost=150000.0
    )

    assert eval_result["new_score"] > eval_result["baseline_score"]
    assert eval_result["delta"] > 0.0
