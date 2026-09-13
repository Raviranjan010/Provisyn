"""Multi-Stage Disruption Cascade Engine for PROVISYN.
Simulates graph-based propagation across 7 sequential stages:
Supplier Failure -> Material Shortage -> Factory Impact -> Production Reduction -> Order Delays -> Customer Impact -> Revenue Exposure.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Any, Optional
import pandas as pd
import networkx as nx
from backend.core.logging import get_logger
from backend.data.repository import BaseRepository
from backend.graph.analytics import build_supply_chain_graph

logger = get_logger(__name__)

@dataclass
class CascadeStage:
    stage_number: int
    name: str
    affected_count: int
    affected_ids: List[str]
    impact_metric: str
    metric_value: float
    description: str

@dataclass
class CascadeResult:
    seed_entities: List[str]
    severity: float
    stages: List[Dict[str, Any]]
    affected_suppliers: List[str]
    affected_materials: List[str]
    affected_factories: List[str]
    affected_products: List[str]
    affected_orders: List[str]
    affected_customers: List[str]
    revenue_at_risk: float
    units_delayed: int

class CascadeEngine:
    """Engine simulating multi-tier propagation of supply shocks through production and fulfillment networks."""

    def __init__(self, repo: BaseRepository):
        self.repo = repo

    def simulate_disruption(
        self,
        seed_entities: List[str],
        severity: float = 1.0,
        max_depth: int = 10,
        attenuation: float = 0.95
    ) -> CascadeResult:
        """Simulate disruption cascade seeded at one or more suppliers or regions.
        Follows the strict 7-stage chain:
        1. Supplier Failure
        2. Material Shortage
        3. Factory Impact
        4. Production Reduction
        5. Order Delays
        6. Customer Impact
        7. Revenue Exposure
        """
        if not seed_entities:
            return CascadeResult(
                seed_entities=[], severity=0.0, stages=[],
                affected_suppliers=[], affected_materials=[], affected_factories=[],
                affected_products=[], affected_orders=[], affected_customers=[],
                revenue_at_risk=0.0, units_delayed=0
            )

        vendors_df = self.repo.get_vendors()
        materials_df = self.repo.get_materials()
        regions_df = self.repo.get_regions()
        po_df = self.repo.get_purchase_orders()
        bom_df = self.repo.get_bill_of_materials()
        factories_df = self.repo.get_factories()
        products_df = self.repo.get_products()
        orders_df = self.repo.get_orders()

        G = build_supply_chain_graph(
            vendors_df, materials_df, regions_df, po_df, bom_df,
            factories_df=factories_df, products_df=products_df, orders_df=orders_df
        )

        # Normalize seed nodes
        active_seeds = set()
        for s in seed_entities:
            clean = s.strip()
            if clean in G.nodes():
                active_seeds.add(clean)
            elif f"V_{clean}" in G.nodes():
                active_seeds.add(f"V_{clean}")
            elif f"R_{clean}" in G.nodes():
                active_seeds.add(f"R_{clean}")

        # Stage 1: Supplier Failure
        affected_suppliers: Set[str] = set()
        for seed in active_seeds:
            ntype = G.nodes[seed].get("node_type")
            if ntype == "vendor":
                affected_suppliers.add(seed.replace("V_", ""))
            elif ntype == "region":
                # Find all vendors in this region
                for u, v, d in G.in_edges(seed, data=True):
                    if d.get("edge_type") == "LOCATED_IN":
                        affected_suppliers.add(u.replace("V_", ""))

        # Stage 2: Material Shortage (walking SUPPLIES + BOM)
        affected_materials: Set[str] = set()
        for sup in affected_suppliers:
            sup_node = f"V_{sup}"
            if sup_node in G.nodes():
                for _, target, d in G.out_edges(sup_node, data=True):
                    if d.get("edge_type") == "SUPPLIES":
                        affected_materials.add(target.replace("M_", ""))

        # Walk BOM hierarchy up to max_depth
        frontier = list(affected_materials)
        depth = 0
        while frontier and depth < max_depth:
            next_frontier = []
            for m in frontier:
                m_node = f"M_{m}"
                # In BOM: parent -> child, so child shortage propagates to parent
                if m_node in G.nodes():
                    for parent, _, d in G.in_edges(m_node, data=True):
                        if d.get("edge_type") == "BOM":
                            parent_m = parent.replace("M_", "")
                            if parent_m not in affected_materials:
                                affected_materials.add(parent_m)
                                next_frontier.append(parent_m)
            frontier = next_frontier
            depth += 1

        # Stage 3: Factory Impact
        affected_factories: Set[str] = set()
        if affected_materials and factories_df is not None and not factories_df.empty:
            # If materials are short, factories consuming semi/raw materials are impacted
            for fid in factories_df["FACTORY_ID"].unique():
                affected_factories.add(str(fid))

        # Stage 4: Production Reduction
        affected_products: Set[str] = set()
        if affected_factories and products_df is not None and not products_df.empty:
            for pid in products_df["PRODUCT_ID"].unique():
                affected_products.add(str(pid))

        # Stage 5: Order Delays
        affected_orders: Set[str] = set()
        affected_customers: Set[str] = set()
        total_revenue_at_risk = 0.0
        total_units_delayed = 0

        if affected_products and orders_df is not None and not orders_df.empty and "PRODUCT_ID" in orders_df.columns:
            matching_orders = orders_df[orders_df["PRODUCT_ID"].isin(affected_products)]
            for _, o in matching_orders.iterrows():
                oid = str(o["ORDER_ID"])
                affected_orders.add(oid)
                affected_customers.add(str(o["CUSTOMER_ID"]))
                # Attenuated revenue exposure based on shock severity
                order_rev = float(o.get("REVENUE", 0.0))
                total_revenue_at_risk += order_rev * min(1.0, severity)
                total_units_delayed += int(o.get("QUANTITY", 0))

        # Construct stage breakdown
        stages_data = [
            {
                "stage_number": 1,
                "name": "Supplier Failure",
                "count": len(affected_suppliers),
                "entities": list(affected_suppliers),
                "impact_text": f"{len(affected_suppliers)} Tier-1 vendors disrupted"
            },
            {
                "stage_number": 2,
                "name": "Material Shortage",
                "count": len(affected_materials),
                "entities": list(affected_materials),
                "impact_text": f"{len(affected_materials)} parts/BOM assemblies starved"
            },
            {
                "stage_number": 3,
                "name": "Factory Impact",
                "count": len(affected_factories),
                "entities": list(affected_factories),
                "impact_text": f"{len(affected_factories)} plants operating at partial line rate"
            },
            {
                "stage_number": 4,
                "name": "Production Reduction",
                "count": len(affected_products),
                "entities": list(affected_products),
                "impact_text": f"{len(affected_products)} vehicle/pack models curtailed"
            },
            {
                "stage_number": 5,
                "name": "Order Delays",
                "count": len(affected_orders),
                "entities": list(affected_orders),
                "impact_text": f"{len(affected_orders)} customer purchase commitments delayed"
            },
            {
                "stage_number": 6,
                "name": "Customer Impact",
                "count": len(affected_customers),
                "entities": list(affected_customers),
                "impact_text": f"{len(affected_customers)} commercial clients facing delivery slip"
            },
            {
                "stage_number": 7,
                "name": "Revenue Exposure",
                "count": int(total_revenue_at_risk),
                "entities": [f"${total_revenue_at_risk:,.0f}"],
                "impact_text": f"${total_revenue_at_risk/1e6:.2f}M estimated revenue exposure"
            },
        ]

        return CascadeResult(
            seed_entities=seed_entities,
            severity=severity,
            stages=stages_data,
            affected_suppliers=list(affected_suppliers),
            affected_materials=list(affected_materials),
            affected_factories=list(affected_factories),
            affected_products=list(affected_products),
            affected_orders=list(affected_orders),
            affected_customers=list(affected_customers),
            revenue_at_risk=round(total_revenue_at_risk, 2),
            units_delayed=total_units_delayed
        )
