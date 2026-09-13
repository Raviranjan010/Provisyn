"""Single Point of Failure (SPOF) and Bottleneck Detection Engine for PROVISYN.
Extends betweenness centrality with alternative-path counting and downstream network blast radius.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import networkx as nx
from backend.core.logging import get_logger
from backend.data.repository import BaseRepository
from backend.graph.analytics import (
    build_supply_chain_graph,
    compute_pagerank,
    compute_betweenness_centrality,
    compute_louvain_communities,
)

logger = get_logger(__name__)

class SPOFEngine:
    """Engine for identifying, ranking, and classifying single points of failure."""

    def __init__(self, repo: BaseRepository):
        self.repo = repo

    def identify_bottlenecks(self) -> pd.DataFrame:
        """Analyze graph topology and supplier redundancy to identify single points of failure.
        Assigns severity tiers: CRITICAL, HIGH, MEDIUM, LOW.
        """
        vendors_df = self.repo.get_vendors()
        materials_df = self.repo.get_materials()
        regions_df = self.repo.get_regions()
        po_df = self.repo.get_purchase_orders()
        bom_df = self.repo.get_bill_of_materials()
        risk_df = self.repo.get_risk_scores()

        if vendors_df.empty or materials_df.empty:
            return pd.DataFrame()

        G = build_supply_chain_graph(vendors_df, materials_df, regions_df, po_df, bom_df)
        pagerank = compute_pagerank(G)
        betweenness = compute_betweenness_centrality(G)
        communities = compute_louvain_communities(G)

        # Risk score mapping
        risk_map = {}
        if not risk_df.empty:
            for _, r in risk_df.iterrows():
                risk_map[f"{r['ENTITY_TYPE'][0]}_{r['ENTITY_ID']}"] = float(r.get("RISK_SCORE", 0.5))

        # Build material supplier redundancy lookup
        mat_suppliers = {}
        if not po_df.empty:
            for _, po in po_df.iterrows():
                mid = str(po["MATERIAL_ID"])
                vid = str(po["VENDOR_ID"])
                mat_suppliers.setdefault(mid, set()).add(vid)

        bottlenecks = []
        now_ts = datetime.now()

        for node in G.nodes():
            n_data = G.nodes[node]
            ntype = n_data.get("node_type", "unknown").upper()
            if ntype not in ["VENDOR", "MATERIAL"]:
                continue

            entity_id = n_data.get("entity_id", node)
            pr = float(pagerank.get(node, 0.0))
            bc = float(betweenness.get(node, 0.0))
            comm = int(communities.get(node, -1))
            score = float(risk_map.get(node, 0.5))

            # Redundancy: alternative paths
            if ntype == "MATERIAL":
                supp_count = len(mat_suppliers.get(entity_id, []))
                alt_paths = max(0, supp_count - 1)
            else:
                # Vendor: how many other suppliers exist for the materials this vendor supplies?
                vendor_materials = [
                    v for u, v, d in G.out_edges(node, data=True)
                    if d.get("edge_type") == "SUPPLIES"
                ]
                if vendor_materials:
                    alt_counts = [len(mat_suppliers.get(m.replace("M_", ""), [])) - 1 for m in vendor_materials]
                    alt_paths = min(alt_counts) if alt_counts else 0
                else:
                    alt_paths = 1

            # Downstream reachability (blast radius in graph)
            try:
                descendants = nx.descendants(G, node)
                affected_size = len(descendants)
            except Exception:
                affected_size = 1

            # Severity tier logic
            if (bc > 0.08 and alt_paths == 0) or (score > 0.70 and alt_paths == 0) or bc > 0.12:
                severity = "CRITICAL"
            elif bc > 0.04 or alt_paths == 0 or (score > 0.60 and alt_paths <= 1):
                severity = "HIGH"
            elif bc > 0.01 or alt_paths <= 2:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            bottlenecks.append({
                "ENTITY_TYPE": ntype,
                "ENTITY_ID": entity_id,
                "BETWEENNESS_SCORE": round(bc, 6),
                "PAGERANK_SCORE": round(pr, 6),
                "RISK_SCORE": round(score, 4),
                "COMMUNITY_ID": comm,
                "ALTERNATIVE_PATH_COUNT": alt_paths,
                "AFFECTED_NETWORK_SIZE": affected_size,
                "SEVERITY_TIER": severity,
                "MODEL_VERSION": "v1.2.0-provisyn",
                "IDENTIFIED_AT": now_ts
            })

        df_b = pd.DataFrame(bottlenecks)
        # Sort by Betweenness and PageRank
        df_b = df_b.sort_values(by=["BETWEENNESS_SCORE", "PAGERANK_SCORE"], ascending=[False, False]).reset_index(drop=True)
        df_b["BOTTLENECK_RANK"] = df_b.index + 1

        self.repo.write_table(df_b, "BOTTLENECKS", overwrite=True)
        return df_b
