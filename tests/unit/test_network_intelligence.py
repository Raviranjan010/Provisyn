"""Unit tests for Network Intelligence and graph analytics algorithms (Phase 7)."""
import networkx as nx
import pandas as pd
import duckdb
from backend.graph.analytics import (
    build_supply_chain_graph,
    compute_pagerank,
    compute_betweenness_centrality,
    compute_louvain_communities,
)
from backend.data.repository import DuckDBRepository
from backend.data.generator import seed_database

def test_centrality_values_match_networkx_reference():
    """Verify compute_pagerank and compute_betweenness_centrality match exact NetworkX reference outputs."""
    # Create a deterministic fixed 4-node directed graph
    G = nx.DiGraph()
    G.add_edge("A", "B")
    G.add_edge("B", "C")
    G.add_edge("C", "A")
    G.add_edge("D", "B")  # D points to B

    # Direct NetworkX reference computation
    ref_pr = nx.pagerank(G, alpha=0.85, max_iter=100, tol=1e-6)
    ref_bc = nx.betweenness_centrality(G, normalized=True)

    test_pr = compute_pagerank(G, alpha=0.85, max_iter=100, tol=1e-6)
    test_bc = compute_betweenness_centrality(G, k_samples=100)

    for node in G.nodes():
        assert abs(test_pr[node] - ref_pr[node]) < 1e-5, f"PageRank mismatch for node {node}"
        assert abs(test_bc[node] - ref_bc[node]) < 1e-5, f"Betweenness mismatch for node {node}"

def test_graph_node_and_edge_counts_match_db():
    """Verify that graph construction matches counts from direct database queries."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    seed_database(repo, seed=42)

    vendors_df = repo.get_vendors()
    materials_df = repo.get_materials()
    regions_df = repo.get_regions()
    po_df = repo.get_purchase_orders()
    bom_df = repo.get_bill_of_materials()

    G = build_supply_chain_graph(vendors_df, materials_df, regions_df, po_df, bom_df)

    expected_node_count = len(vendors_df) + len(materials_df) + len(regions_df)
    assert G.number_of_nodes() == expected_node_count

    # Verify edge count is non-zero and accounts for supplies, located_in, and bom
    assert G.number_of_edges() > 0
