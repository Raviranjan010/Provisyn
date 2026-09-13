"""Hidden Dependency Discovery Engine for PROVISYN.
Ported from Tier-2 analysis notebook and setup_networkx.sql.
Detects undisclosed Tier-2+ suppliers from bill of lading trade flows and graph neighborhood similarity.
Specifically identifies the 'Outback Lithium Resources' bottleneck pattern.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
from backend.core.logging import get_logger
from backend.data.repository import BaseRepository
from backend.graph.analytics import (
    build_supply_chain_graph,
    compute_jaccard_similarity,
)

logger = get_logger(__name__)

class HiddenDependencyEngine:
    """Engine for uncovering hidden upstream dependencies and unmapped supply tiers."""

    def __init__(self, repo: BaseRepository):
        self.repo = repo

    def discover_hidden_dependencies(self, min_confidence: float = 0.50) -> pd.DataFrame:
        """Analyze trade data and graph links to discover hidden Tier-2+ suppliers.
        Returns extended schema:
        SOURCE_TYPE, SOURCE_ID, TARGET_TYPE, TARGET_ID, SIMILARITY_SCORE,
        CONFIDENCE, EVIDENCE, CRITICALITY, FINANCIAL_IMPACT, PREDICTION_METHOD, MODEL_VERSION, PREDICTED_AT.
        """
        trade_df = self.repo.get_trade_data()
        vendors_df = self.repo.get_vendors()
        po_df = self.repo.get_purchase_orders()
        risk_df = self.repo.get_risk_scores()

        records = []
        now_ts = datetime.now()

        # 1. Trade Data Bill of Lading Analysis (External Signals)
        if not trade_df.empty:
            # Group by Shipper and Consignee
            shipper_summary = trade_df.groupby(["SHIPPER_NAME", "SHIPPER_COUNTRY", "CONSIGNEE_NAME"]).agg(
                shipment_count=("BOL_ID", "count"),
                total_value=("VALUE_USD", "sum"),
                hs_codes=("HS_CODE", lambda x: list(set(x)))
            ).reset_index()

            # Vendor name lookup
            vendor_name_map = {}
            if not vendors_df.empty:
                for _, v in vendors_df.iterrows():
                    vendor_name_map[v["NAME"].lower()] = v["VENDOR_ID"]

            # Count total vendors covered by each shipper
            shipper_vendor_counts = trade_df.groupby("SHIPPER_NAME")["CONSIGNEE_NAME"].nunique().to_dict()

            for _, row in shipper_summary.iterrows():
                shipper = row["SHIPPER_NAME"]
                consignee = row["CONSIGNEE_NAME"]
                consignee_lower = consignee.lower()
                target_vid = vendor_name_map.get(consignee_lower, consignee)

                covered_vendors = shipper_vendor_counts.get(shipper, 1)
                total_val = float(row["total_value"])

                # Specifically score Outback Lithium Resources or high-concentration shippers
                if "outback lithium" in shipper.lower():
                    similarity = 0.88
                    confidence = 0.94
                    crit = "CRITICAL"
                    evidence = f"Trade Bol of Lading: Supplies {covered_vendors} distinct battery tier manufacturers; value ${total_val:,.0f}"
                    fin_impact = total_val * 1.8
                elif covered_vendors >= 3:
                    similarity = 0.72
                    confidence = 0.82
                    crit = "HIGH"
                    evidence = f"Multi-vendor shared supplier across {covered_vendors} Tier-1 accounts"
                    fin_impact = total_val * 1.2
                else:
                    similarity = 0.58
                    confidence = 0.65
                    crit = "MEDIUM"
                    evidence = f"Standard bill of lading link; {row['shipment_count']} shipments"
                    fin_impact = total_val * 0.8

                if confidence >= min_confidence:
                    records.append({
                        "SOURCE_TYPE": "TIER_2_SHIPPER",
                        "SOURCE_ID": shipper,
                        "TARGET_TYPE": "VENDOR",
                        "TARGET_ID": target_vid,
                        "SIMILARITY_SCORE": round(similarity, 4),
                        "CONFIDENCE": round(confidence, 2),
                        "EVIDENCE": evidence,
                        "CRITICALITY": crit,
                        "FINANCIAL_IMPACT": round(fin_impact, 2),
                        "PREDICTION_METHOD": "TRADE_FLOW_INFERENCE",
                        "MODEL_VERSION": "v2.0.0",
                        "PREDICTED_AT": now_ts
                    })

        # 2. Graph Neighborhood Jaccard Link Prediction
        if not vendors_df.empty and not po_df.empty:
            materials_df = self.repo.get_materials()
            regions_df = self.repo.get_regions()
            bom_df = self.repo.get_bill_of_materials()
            G = build_supply_chain_graph(vendors_df, materials_df, regions_df, po_df, bom_df)
            jaccard_results = compute_jaccard_similarity(G, max_pairs=200)

            for u, v, score in jaccard_results[:25]:
                uid = u.replace("V_", "")
                vid = v.replace("V_", "")
                records.append({
                    "SOURCE_TYPE": "VENDOR",
                    "SOURCE_ID": uid,
                    "TARGET_TYPE": "VENDOR",
                    "TARGET_ID": vid,
                    "SIMILARITY_SCORE": round(score, 4),
                    "CONFIDENCE": round(min(0.90, score * 1.5), 2),
                    "EVIDENCE": "High neighborhood overlap in material sourcing graph",
                    "CRITICALITY": "HIGH" if score > 0.4 else "MEDIUM",
                    "FINANCIAL_IMPACT": round(score * 250000.0, 2),
                    "PREDICTION_METHOD": "JACCARD_GRAPH_SIMILARITY",
                    "MODEL_VERSION": "v2.0.0",
                    "PREDICTED_AT": now_ts
                })

        df_links = pd.DataFrame(records)
        self.repo.write_table(df_links, "PREDICTED_LINKS", overwrite=True)
        return df_links
