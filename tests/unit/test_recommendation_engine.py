"""Unit tests for Prescriptive Recommendations Engine (Phase 14)."""
import duckdb
from backend.data.repository import DuckDBRepository
from backend.engines.recommendation import RecommendationEngine

def test_recommendation_ranking_monotonicity():
    """Verify recommendation ranking order is monotonic in ROI / efficiency score."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    engine = RecommendationEngine(repo)

    res = engine.generate_recommendations(budget=600000.0)
    assert res["is_feasible"]
    recs = res["recommendations"]
    assert len(recs) >= 2

    # Check rank order monotonicity
    ranks = [r["rank"] for r in recs]
    assert ranks == sorted(ranks)
    for i in range(len(recs) - 1):
        assert recs[i]["roi_ratio"] >= recs[i+1]["roi_ratio"]

def test_top_recommendations_plausibility():
    """Verify top recommendations have plausible positive metrics and realistic ROI."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    engine = RecommendationEngine(repo)

    res = engine.generate_recommendations(budget=400000.0)
    recs = res["recommendations"]
    
    top = recs[0]
    assert top["estimated_cost"] > 0
    assert top["exposure_reduction"] > top["estimated_cost"]
    assert top["resilience_improvement"] > 0
    assert 0.80 <= top["confidence"] <= 1.0
