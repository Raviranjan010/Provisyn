"""End-to-End Integration Test for PROVISYN Decision Intelligence Pipeline.
Per testing_and_security.md:
Exercises the complete data-to-decision pipeline:
Seed DuckDB -> Multi-Tier Risk Scoring -> Scenario Simulation -> Cascade Traversal ->
Financial Exposure (P10 <= P50 <= P90) -> Resilience Delta -> Prescriptive Optimization.
"""
import pytest
import duckdb
from backend.data.repository import DuckDBRepository
from backend.data.generator import seed_database
from backend.engines.risk import RiskEngine
from backend.engines.spof import SPOFEngine
from backend.engines.cascade import CascadeEngine
from backend.engines.financial import FinancialExposureEngine
from backend.engines.resilience import ResilienceEngine
from backend.engines.simulation import SimulationEngine
from backend.engines.optimization import OptimizationEngine
from backend.engines.recommendation import RecommendationEngine

@pytest.fixture
def in_memory_repo():
    """Create an isolated in-memory DuckDB repository seeded with synthetic supply chain data."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    success = seed_database(repo, seed=42, overwrite=True)
    assert success, "Database seeding must succeed"
    return repo

def test_full_decision_intelligence_pipeline_e2e(in_memory_repo):
    """Verify that all analytical engines interoperate consistently on seeded data."""
    repo = in_memory_repo

    # 1. Verify Master Data Seed
    vendors_df = repo.get_vendors()
    materials_df = repo.get_materials()
    orders_df = repo.get_orders()
    assert not vendors_df.empty, "VENDORS table should not be empty"
    assert not materials_df.empty, "MATERIALS table should not be empty"
    assert not orders_df.empty, "ORDERS table should not be empty"

    # 2. Risk Engine: Compute Multi-Tier Risk Scores
    risk_engine = RiskEngine(repo)
    risk_df = risk_engine.compute_risk_scores()
    assert not risk_df.empty, "Risk scores must be computed"
    assert (risk_df["RISK_SCORE"] >= 0.0).all() and (risk_df["RISK_SCORE"] <= 1.0).all(), \
        "All risk scores must lie within [0.0, 1.0]"

    # 3. SPOF Engine: Identify Bottlenecks
    spof_engine = SPOFEngine(repo)
    spof_df = spof_engine.identify_bottlenecks()
    assert not spof_df.empty, "Network topology should identify structural bottlenecks"
    assert "SEVERITY_TIER" in spof_df.columns or "SEVERITY" in spof_df.columns

    # 4. Simulation Engine: Monte Carlo Disruption Scenario
    sim_engine = SimulationEngine(repo)
    sim_res = sim_engine.run_scenario(
        scenario_type="SUPPLIER_FAILURE",
        target_entities=["V10001"],  # Outback Lithium
        intensity=0.85,
        duration_days=45,
        n_iterations=50
    )

    # Verify Monte Carlo ordering
    p10 = sim_res.monte_carlo_p10
    p50 = sim_res.monte_carlo_p50
    p90 = sim_res.monte_carlo_p90
    assert p10 <= p50 <= p90, f"Monte Carlo percentiles must satisfy P10 ({p10}) <= P50 ({p50}) <= P90 ({p90})"
    assert sim_res.cascade.total_affected_entities > 0, "Cascade blast radius must be non-zero"

    # 5. Resilience Engine: Score Delta Verification
    res_engine = ResilienceEngine(repo)
    baseline_res = res_engine.calculate_resilience_score(
        redundancy_ratio=0.75,
        mean_risk_score=float(risk_df["RISK_SCORE"].mean()),
        days_of_cover=30.0,
        exposure_usd=3500000.0,
        total_revenue_usd=50000000.0
    )
    assert 0 <= baseline_res["resilience_score"] <= 100, "Resilience score must be bounded [0, 100]"

    # 6. Optimization & Prescriptive Recommendations
    opt_engine = OptimizationEngine(repo)
    budget = 500000.0
    opt_out = opt_engine.optimize_allocations(budget=budget)
    assert opt_out.is_feasible, "Optimization problem must be feasible for $500k budget"
    assert opt_out.total_spend <= budget, f"Total spend ({opt_out.total_spend}) must not exceed budget ({budget})"
    assert opt_out.total_exposure_reduction > 0, "Exposure reduction must be positive"
    assert opt_out.total_resilience_gain > 0, "Resilience gain must be positive"

    # 7. Recommendation Engine Persistence
    rec_engine = RecommendationEngine(repo)
    rec_result = rec_engine.generate_recommendations(budget=budget)
    assert rec_result["is_feasible"]
    saved_recs = repo.get_recommendations()
    assert not saved_recs.empty, "Selected actions must be persisted into RECOMMENDATIONS repository table"
