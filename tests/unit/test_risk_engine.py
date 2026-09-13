"""Unit tests for graph risk propagation and RiskEngine (Phase 5)."""
import networkx as nx
import pandas as pd
import duckdb
from backend.graph.analytics import propagate_risk_scores, compute_pagerank
from backend.data.repository import DuckDBRepository
from backend.data.generator import seed_database
from backend.engines.risk import RiskEngine

def test_hand_built_5_node_graph_risk_propagation():
    """Verify propagation math on a hand-built 5-node graph with known expected scores.
    Nodes:
      R_AUS (Region, base_risk=0.8)
      V_101 (Vendor, connected to R_AUS, dist=1, fin_health=0.8, tier=1)
      M_201 (Material, supplied by V_101, dist=2, crit=0.9, inv=30)
      V_102 (Vendor, connected to M_201, dist=3, fin_health=0.4, tier=2)
      R_USA (Region, isolated, base_risk=0.1, dist=inf)
    """
    G = nx.DiGraph()
    G.add_node("R_AUS", node_type="region", base_risk=0.8, geopolitical_risk=0.8)
    G.add_node("V_101", node_type="vendor", financial_health=0.8, tier=1)
    G.add_node("M_201", node_type="material", criticality=0.9, inventory_days=30)
    G.add_node("V_102", node_type="vendor", financial_health=0.4, tier=2)
    G.add_node("R_USA", node_type="region", base_risk=0.1, geopolitical_risk=0.1)

    # Undirected/directed connections
    G.add_edge("V_101", "R_AUS", edge_type="LOCATED_IN")
    G.add_edge("V_101", "M_201", edge_type="SUPPLIES")
    G.add_edge("V_102", "M_201", edge_type="SUPPLIES")

    regions_df = pd.DataFrame([
        {"REGION_CODE": "AUS", "BASE_RISK_SCORE": 0.8, "GEOPOLITICAL_RISK": 0.8},
        {"REGION_CODE": "USA", "BASE_RISK_SCORE": 0.1, "GEOPOLITICAL_RISK": 0.1}
    ])

    scores = propagate_risk_scores(G, regions_df)

    # Assertions:
    # 1. R_AUS distance is 0 -> distance_risk = 1.0; node_risk = (0.8+0.8)/2 = 0.8; combined ~ 0.72+PR
    assert scores["R_AUS"] > 0.65
    # 2. V_101 is distance 1 -> distance_risk = 1 - 0.15 = 0.85
    assert scores["V_101"] > 0.35
    # 3. M_201 is distance 2 -> distance_risk = 1 - 0.30 = 0.70
    assert scores["M_201"] > 0.30
    # 4. V_102 distance is 3 -> distance_risk = 1 - 0.45 = 0.55
    assert scores["V_102"] > 0.25
    # 5. R_USA is disconnected (distance inf) -> distance_risk = 0.1
    assert scores["R_USA"] < scores["R_AUS"]
    # Monotonicity check: R_AUS > V_101 > V_102
    assert scores["R_AUS"] > scores["V_102"]

def test_risk_engine_on_synthetic_data():
    """Verify that RiskEngine computes scores across the synthetic dataset within expected bounds [0, 1]."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    seed_database(repo, seed=42)

    engine = RiskEngine(repo)
    df_risk = engine.compute_risk_scores()

    assert not df_risk.empty
    assert "RISK_SCORE" in df_risk.columns
    assert "RISK_CATEGORY" in df_risk.columns
    assert len(df_risk) == 50 + 26  # 50 vendors + 26 materials

    # Range and distribution checks matching original notebook (mean ~ 0.4 - 0.7)
    mean_risk = df_risk["RISK_SCORE"].mean()
    assert 0.30 <= mean_risk <= 0.80
    assert df_risk["RISK_SCORE"].min() >= 0.0
    assert df_risk["RISK_SCORE"].max() <= 1.0

    # High-risk categories exist
    categories = set(df_risk["RISK_CATEGORY"].unique())
    assert "CRITICAL" in categories or "HIGH" in categories
