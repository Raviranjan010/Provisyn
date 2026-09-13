"""Unit tests for Hidden Dependency Discovery and SPOF Detection (Phase 8)."""
import duckdb
import pandas as pd
from backend.data.repository import DuckDBRepository
from backend.data.generator import seed_database
from backend.engines.hidden_dependency import HiddenDependencyEngine
from backend.engines.spof import SPOFEngine

def test_outback_lithium_resources_hidden_dependency_detected():
    """Verify that the synthetic 'Outback Lithium Resources' pattern is detected by the engine."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    seed_database(repo, seed=42)

    engine = HiddenDependencyEngine(repo)
    df_hidden = engine.discover_hidden_dependencies()

    assert not df_hidden.empty
    assert "SOURCE_ID" in df_hidden.columns
    assert "CRITICALITY" in df_hidden.columns

    # Verify Outback Lithium is identified
    outback_matches = df_hidden[df_hidden["SOURCE_ID"].str.contains("Outback Lithium", case=False, na=False)]
    assert not outback_matches.empty, "Outback Lithium Resources pattern must be detected"
    
    first_outback = outback_matches.iloc[0]
    assert first_outback["CRITICALITY"] == "CRITICAL"
    assert first_outback["CONFIDENCE"] >= 0.85

def test_spof_ranking_severity_tiers():
    """Verify SPOF engine assigns Critical/High/Medium/Low severity tiers and ranks properly."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    seed_database(repo, seed=42)

    spof_engine = SPOFEngine(repo)
    df_spof = spof_engine.identify_bottlenecks()

    assert not df_spof.empty
    assert "SEVERITY_TIER" in df_spof.columns
    assert "BOTTLENECK_RANK" in df_spof.columns
    assert "ALTERNATIVE_PATH_COUNT" in df_spof.columns

    # Tiers check
    tiers = set(df_spof["SEVERITY_TIER"].unique())
    assert "CRITICAL" in tiers or "HIGH" in tiers

    # Top bottleneck has rank 1
    top_row = df_spof.iloc[0]
    assert top_row["BOTTLENECK_RANK"] == 1
    assert top_row["BETWEENNESS_SCORE"] >= 0.0
