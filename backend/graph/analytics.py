"""Graph analytics engine for PROVISYN.
Ported directly from notebooks/graphsage_supply_chain_risk.ipynb.
Provides deterministic, testable graph construction, centrality, community detection,
Jaccard link prediction, and rule-based risk propagation.
"""
import time
from typing import Dict, List, Tuple, Any, Optional
import networkx as nx
from networkx.algorithms import community as nx_community
import pandas as pd
import numpy as np
from backend.core.logging import get_logger

logger = get_logger(__name__)

def build_supply_chain_graph(
    vendors_df: pd.DataFrame,
    materials_df: pd.DataFrame,
    regions_df: pd.DataFrame,
    purchase_orders_df: pd.DataFrame,
    bom_df: pd.DataFrame,
    factories_df: Optional[pd.DataFrame] = None,
    products_df: Optional[pd.DataFrame] = None,
    orders_df: Optional[pd.DataFrame] = None,
) -> nx.DiGraph:
    """Build heterogeneous directed supply chain graph matching notebooks/graphsage_supply_chain_risk.ipynb."""
    G = nx.DiGraph()

    # Add vendor nodes
    for _, row in vendors_df.iterrows():
        vid = str(row["VENDOR_ID"])
        G.add_node(
            f"V_{vid}",
            node_type="vendor",
            entity_id=vid,
            name=row.get("NAME", f"Vendor {vid}"),
            country=row.get("COUNTRY_CODE", ""),
            tier=int(row.get("TIER", 1)),
            financial_health=float(row.get("FINANCIAL_HEALTH_SCORE", 0.5)),
            reliability=float(row.get("RELIABILITY_SCORE", 0.85))
        )

    # Add material nodes
    for _, row in materials_df.iterrows():
        mid = str(row["MATERIAL_ID"])
        G.add_node(
            f"M_{mid}",
            node_type="material",
            entity_id=mid,
            description=row.get("DESCRIPTION", mid),
            material_group=row.get("MATERIAL_GROUP", "RAW"),
            criticality=float(row.get("CRITICALITY_SCORE", 0.5)),
            inventory_days=int(row.get("INVENTORY_DAYS", 30)),
            unit_cost=float(row.get("UNIT_COST", 50.0)),
            lead_time_days=int(row.get("LEAD_TIME_DAYS", 21))
        )

    # Add region nodes
    for _, row in regions_df.iterrows():
        rcode = str(row["REGION_CODE"])
        G.add_node(
            f"R_{rcode}",
            node_type="region",
            entity_id=rcode,
            name=row.get("REGION_NAME", rcode),
            base_risk=float(row.get("BASE_RISK_SCORE", 0.0)),
            geopolitical_risk=float(row.get("GEOPOLITICAL_RISK", 0.0)),
            natural_disaster_risk=float(row.get("NATURAL_DISASTER_RISK", 0.0)),
            infrastructure_score=float(row.get("INFRASTRUCTURE_SCORE", 0.5))
        )

    # Extended nodes (Factories, Products, Orders)
    if factories_df is not None and not factories_df.empty:
        for _, row in factories_df.iterrows():
            fid = str(row["FACTORY_ID"])
            G.add_node(
                f"F_{fid}",
                node_type="factory",
                entity_id=fid,
                region=row.get("REGION_CODE", ""),
                capacity=float(row.get("CAPACITY", 1000.0)),
                product_id=row.get("PRODUCT_ID", "")
            )

    if products_df is not None and not products_df.empty:
        for _, row in products_df.iterrows():
            pid = str(row["PRODUCT_ID"])
            G.add_node(
                f"P_{pid}",
                node_type="product",
                entity_id=pid,
                name=row.get("NAME", pid),
                revenue_per_unit=float(row.get("REVENUE_PER_UNIT", 1000.0))
            )

    if orders_df is not None and not orders_df.empty:
        for _, row in orders_df.iterrows():
            oid = str(row["ORDER_ID"])
            G.add_node(
                f"ORD_{oid}",
                node_type="order",
                entity_id=oid,
                product_id=row.get("PRODUCT_ID", ""),
                revenue=float(row.get("REVENUE", 10000.0)),
                due_date=str(row.get("DUE_DATE", ""))
            )

    # Add SUPPLIES edges (Vendor -> Material)
    for _, row in purchase_orders_df.iterrows():
        src = f"V_{row['VENDOR_ID']}"
        dst = f"M_{row['MATERIAL_ID']}"
        if src in G.nodes and dst in G.nodes:
            weight = float(row.get("QUANTITY", 1) * row.get("UNIT_PRICE", 1.0))
            if G.has_edge(src, dst):
                G[src][dst]["weight"] += weight
            else:
                G.add_edge(src, dst, edge_type="SUPPLIES", weight=weight)

    # Add LOCATED_IN edges (Vendor -> Region)
    for _, row in vendors_df.iterrows():
        src = f"V_{row['VENDOR_ID']}"
        dst = f"R_{row['COUNTRY_CODE']}"
        if src in G.nodes and dst in G.nodes:
            G.add_edge(src, dst, edge_type="LOCATED_IN", weight=1.0)

    # Add BOM edges (Material -> Material)
    for _, row in bom_df.iterrows():
        src = f"M_{row['PARENT_MATERIAL_ID']}"
        dst = f"M_{row['CHILD_MATERIAL_ID']}"
        if src in G.nodes and dst in G.nodes:
            weight = float(row.get("QUANTITY_PER_UNIT", 1.0))
            G.add_edge(src, dst, edge_type="BOM", weight=weight)

    # Add PRODUCES edges (Factory -> Product)
    if factories_df is not None and not factories_df.empty:
        for _, row in factories_df.iterrows():
            src = f"F_{row['FACTORY_ID']}"
            dst = f"P_{row['PRODUCT_ID']}"
            if src in G.nodes and dst in G.nodes:
                G.add_edge(src, dst, edge_type="PRODUCES", weight=1.0)

    # Add FULFILLS edges (Product -> Order)
    if orders_df is not None and not orders_df.empty:
        for _, row in orders_df.iterrows():
            src = f"P_{row['PRODUCT_ID']}"
            dst = f"ORD_{row['ORDER_ID']}"
            if src in G.nodes and dst in G.nodes:
                G.add_edge(src, dst, edge_type="FULFILLS", weight=float(row.get("REVENUE", 1.0)))

    logger.debug(f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G

def compute_pagerank(G: nx.DiGraph, alpha: float = 0.85, max_iter: int = 100, tol: float = 1e-6) -> Dict[str, float]:
    """Compute PageRank scores for all nodes."""
    if G.number_of_nodes() == 0:
        return {}
    return nx.pagerank(G, alpha=alpha, max_iter=max_iter, tol=tol)

def compute_betweenness_centrality(G: nx.DiGraph, k_samples: int = 100) -> Dict[str, float]:
    """Compute normalized betweenness centrality."""
    if G.number_of_nodes() == 0:
        return {}
    k = min(k_samples, G.number_of_nodes())
    return nx.betweenness_centrality(G, k=k, normalized=True)

def compute_louvain_communities(G: nx.DiGraph) -> Dict[str, int]:
    """Identify supply chain clusters using Louvain community detection."""
    if G.number_of_nodes() == 0:
        return {}
    G_undirected = G.to_undirected()
    try:
        communities = nx_community.louvain_communities(G_undirected, resolution=1.0, seed=42)
    except Exception as e:
        logger.warning(f"Louvain community detection failed, fallback to connected components: {e}")
        communities = list(nx.connected_components(G_undirected))
    
    node_to_comm = {}
    for idx, comm in enumerate(communities):
        for node in comm:
            node_to_comm[node] = idx
    return node_to_comm

def compute_jaccard_similarity(G: nx.DiGraph, max_pairs: int = 1000) -> List[Tuple[str, str, float]]:
    """Compute Jaccard similarity for non-adjacent vendor pairs."""
    vendor_nodes = [n for n in G.nodes if G.nodes[n].get("node_type") == "vendor"]
    if len(vendor_nodes) < 2:
        return []
    
    G_undirected = G.to_undirected()
    pairs = []
    for i, v1 in enumerate(vendor_nodes):
        for v2 in vendor_nodes[i+1:]:
            if not G.has_edge(v1, v2) and not G.has_edge(v2, v1):
                pairs.append((v1, v2))
    
    if len(pairs) > max_pairs:
        import random
        random.seed(42)
        pairs = random.sample(pairs, max_pairs)
        
    scores = list(nx.jaccard_coefficient(G_undirected, pairs))
    significant = [(u, v, score) for u, v, score in scores if score > 0]
    significant.sort(key=lambda x: x[2], reverse=True)
    return significant

def propagate_risk_scores(
    G: nx.DiGraph,
    regions_df: pd.DataFrame,
    pagerank: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """Propagate regional risk across graph weighted by node attributes and centrality.
    Matches exact formulas from notebook graphsage_supply_chain_risk.ipynb.
    """
    if G.number_of_nodes() == 0:
        return {}
    
    if pagerank is None:
        pagerank = compute_pagerank(G)
        
    G_undirected = G.to_undirected()
    
    # Identify high risk region source
    if not regions_df.empty and "BASE_RISK_SCORE" in regions_df.columns:
        high_risk_row = regions_df.nlargest(1, "BASE_RISK_SCORE").iloc[0]
        source_node = f"R_{high_risk_row['REGION_CODE']}"
    else:
        source_node = None
        
    distances: Dict[str, int] = {}
    if source_node and source_node in G_undirected.nodes:
        try:
            distances = nx.single_source_shortest_path_length(G_undirected, source_node)
        except Exception:
            distances = {}
            
    if not distances:
        # Fallback multi-source BFS from all region nodes
        region_nodes = [n for n in G.nodes if G.nodes[n].get("node_type") == "region"]
        for r in region_nodes:
            try:
                d = nx.single_source_shortest_path_length(G_undirected, r)
                for node, dist in d.items():
                    if node not in distances or dist < distances[node]:
                        distances[node] = dist
            except Exception:
                pass

    risk_scores: Dict[str, float] = {}
    for node in G.nodes:
        node_data = G.nodes[node]
        node_type = node_data.get("node_type", "unknown")
        
        distance = distances.get(node, float("inf"))
        if distance == float("inf"):
            distance_risk = 0.1
        else:
            distance_risk = max(0.0, 1.0 - (distance * 0.15))
            
        if node_type == "vendor":
            financial_health = node_data.get("financial_health", 0.5)
            tier = node_data.get("tier", 1)
            node_risk = (1.0 - financial_health) * 0.3 + (tier / 3.0) * 0.2
        elif node_type == "material":
            criticality = node_data.get("criticality", 0.5)
            inventory = node_data.get("inventory_days", 30)
            node_risk = criticality * 0.3 + max(0.0, (30.0 - inventory) / 30.0) * 0.2
        elif node_type == "region":
            base_risk = node_data.get("base_risk", 0.5)
            geo_risk = node_data.get("geopolitical_risk", 0.5)
            node_risk = (base_risk + geo_risk) / 2.0
        else:
            node_risk = 0.5
            
        pr = pagerank.get(node, 0.0)
        pr_scale = min(100.0, float(len(G))) if len(G) > 0 else 100.0
        combined = distance_risk * 0.4 + node_risk * 0.4 + pr * pr_scale * 0.2
        risk_scores[node] = float(min(1.0, max(0.0, combined)))
        
    return risk_scores
