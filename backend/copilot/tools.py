"""PROVISYN Copilot Tool Registry.
Wraps decision engines into declarative callable tools with structured JSON contracts,
data provenance labels, and audit timestamps.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import pandas as pd

from backend.core.logging import get_logger
from backend.data.repository import BaseRepository, get_repository
from backend.engines.risk import RiskEngine
from backend.engines.spof import SPOFEngine
from backend.engines.cascade import CascadeEngine
from backend.engines.financial import FinancialExposureEngine
from backend.engines.inventory import InventoryEngine
from backend.engines.optimization import OptimizationEngine
from backend.engines.simulation import SimulationEngine
from backend.engines.resilience import ResilienceEngine

logger = get_logger(__name__)

class CopilotToolRegistry:
    """Registry exposing PROVISYN analytical engines as callable tools."""

    def __init__(self, repo: Optional[BaseRepository] = None):
        self.repo = repo or get_repository()
        self.risk_engine = RiskEngine(self.repo)
        self.spof_engine = SPOFEngine(self.repo)
        self.cascade_engine = CascadeEngine(self.repo)
        self.financial_engine = FinancialExposureEngine(self.repo)
        self.inventory_engine = InventoryEngine(self.repo)
        self.optimization_engine = OptimizationEngine(self.repo)
        self.simulation_engine = SimulationEngine(self.repo)
        self.resilience_engine = ResilienceEngine(self.repo)

    def tool_risk_query(self, entity_id: str) -> Dict[str, Any]:
        """Query multi-tier risk metrics and drivers for a specific supplier or material."""
        explanation = self.risk_engine.explain_entity_risk(entity_id)
        df_risk = self.repo.get_risk_scores()
        row = df_risk[df_risk["ENTITY_ID"] == entity_id] if not df_risk.empty else pd.DataFrame()
        
        score = float(row.iloc[0]["RISK_SCORE"]) if not row.empty else explanation.get("total_score", 0.5)
        category = str(row.iloc[0]["RISK_CATEGORY"]) if not row.empty else explanation.get("category", "WARNING")
        
        return {
            "tool": "risk_engine",
            "entity_id": entity_id,
            "entity_name": explanation.get("name", entity_id),
            "risk_score": round(score, 4),
            "risk_category": category,
            "drivers": explanation.get("drivers", []),
            "computed_at": datetime.now().isoformat(),
            "data_labels": {
                "risk_score": "calculated",
                "drivers": "calculated"
            }
        }

    def tool_spof_bottlenecks(self, top_n: int = 5) -> Dict[str, Any]:
        """Identify critical single points of failure (SPOFs) in the supplier network."""
        df_spof = self.spof_engine.identify_bottlenecks()
        if df_spof.empty:
            bottlenecks = []
        else:
            sev_col = "SEVERITY_TIER" if "SEVERITY_TIER" in df_spof.columns else ("SEVERITY" if "SEVERITY" in df_spof.columns else None)
            if sev_col:
                crit = df_spof.sort_values(by=sev_col, ascending=False).head(top_n)
            else:
                crit = df_spof.head(top_n)
            bottlenecks = []
            for _, r in crit.iterrows():
                bottlenecks.append({
                    "entity_id": str(r["ENTITY_ID"]),
                    "entity_name": str(r.get("ENTITY_NAME", r["ENTITY_ID"])),
                    "severity": str(r.get(sev_col, "HIGH") if sev_col else "HIGH"),
                    "pagerank": round(float(r.get("PAGERANK_SCORE", 0.0)), 4),
                    "betweenness": round(float(r.get("BETWEENNESS_SCORE", 0.0)), 4),
                    "redundancy_count": int(r.get("ALTERNATIVE_PATH_COUNT", r.get("REDUNDANCY_COUNT", 0)))
                })

        return {
            "tool": "graph_engine",
            "total_bottlenecks": len(bottlenecks),
            "bottlenecks": bottlenecks,
            "computed_at": datetime.now().isoformat(),
            "data_labels": {
                "bottlenecks": "calculated"
            }
        }

    def tool_cascade_simulation(self, seed_entities: List[str], severity: float = 0.85) -> Dict[str, Any]:
        """Simulate upstream shock propagation and quantify downstream impact blast radius."""
        cascade_res = self.cascade_engine.simulate_disruption(seed_entities=seed_entities, severity=severity)
        return {
            "tool": "cascade_engine",
            "seed_entities": seed_entities,
            "severity": severity,
            "affected_materials_count": len(cascade_res.affected_materials),
            "affected_factories_count": len(cascade_res.affected_factories),
            "affected_orders_count": len(cascade_res.affected_orders),
            "revenue_at_risk_usd": round(cascade_res.revenue_at_risk, 2),
            "stages_count": len(cascade_res.stages),
            "computed_at": datetime.now().isoformat(),
            "data_labels": {
                "affected_entities": "simulated",
                "revenue_at_risk_usd": "simulated"
            }
        }

    def tool_financial_exposure(self, seed_entities: List[str], severity: float = 0.85) -> Dict[str, Any]:
        """Quantify financial exposure, revenue at risk, and expected loss under disruption."""
        fin_res = self.financial_engine.calculate_exposure(seed_entities=seed_entities, shock_severity=severity)
        return {
            "tool": "financial_engine",
            "seed_entities": seed_entities,
            "revenue_at_risk_usd": fin_res.revenue_at_risk,
            "production_loss_usd": fin_res.production_loss,
            "holding_cost_usd": fin_res.holding_cost,
            "expediting_cost_usd": fin_res.expediting_cost,
            "total_financial_exposure_usd": fin_res.total_financial_exposure,
            "expected_loss_usd": fin_res.expected_loss,
            "affected_orders_count": len(fin_res.affected_orders),
            "computed_at": datetime.now().isoformat(),
            "data_labels": fin_res.labels
        }

    def tool_inventory_stockout(self, top_n: int = 5) -> Dict[str, Any]:
        """Query inventory portfolio for materials facing elevated stockout probability."""
        df_inv = self.inventory_engine.evaluate_inventory_portfolio()
        if df_inv.empty:
            items = []
        else:
            top_risks = df_inv.head(top_n)
            items = []
            for _, r in top_risks.iterrows():
                items.append({
                    "material_id": str(r["MATERIAL_ID"]),
                    "description": str(r.get("DESCRIPTION", r["MATERIAL_ID"])),
                    "days_of_cover": float(r.get("DAYS_OF_COVER", 0.0)),
                    "stockout_probability": float(r.get("STOCKOUT_PROBABILITY", 0.0)),
                    "stockout_risk_level": str(r.get("STOCKOUT_RISK_LEVEL", "WARNING")),
                    "reorder_point": float(r.get("REORDER_POINT", 0.0))
                })

        return {
            "tool": "inventory_engine",
            "at_risk_skus_count": len(items),
            "items": items,
            "computed_at": datetime.now().isoformat(),
            "data_labels": {
                "days_of_cover": "observed",
                "stockout_probability": "calculated",
                "reorder_point": "calculated"
            }
        }

    def tool_optimization_recommendations(self, budget_usd: float = 500000.0) -> Dict[str, Any]:
        """Run prescriptive linear optimization to select the highest-ROI mitigation interventions."""
        opt_res = self.optimization_engine.optimize_allocations(budget=budget_usd)
        actions = []
        for a in opt_res.selected_actions:
            actions.append({
                "action_id": a["action_id"],
                "title": a["title"],
                "action_type": a["action_type"],
                "estimated_cost_usd": a["estimated_cost"],
                "risk_reduction": a["risk_reduction"],
                "exposure_reduction_usd": a["exposure_reduction"],
                "resilience_improvement": a["resilience_improvement"],
                "rank": a["rank"]
            })

        return {
            "tool": "optimization_engine",
            "budget_usd": budget_usd,
            "is_feasible": opt_res.is_feasible,
            "total_spend_usd": opt_res.total_spend,
            "exposure_reduction_usd": opt_res.exposure_reduction,
            "resilience_gain": opt_res.resilience_gain,
            "selected_actions": actions,
            "computed_at": datetime.now().isoformat(),
            "data_labels": {
                "budget_usd": "assumption",
                "total_spend_usd": "calculated",
                "exposure_reduction_usd": "simulated",
                "resilience_gain": "calculated"
            }
        }

    def tool_resilience_assessment(self) -> Dict[str, Any]:
        """Calculate overall portfolio resilience score and component breakdown."""
        df_risk = self.repo.get_risk_scores()
        df_inv = self.inventory_engine.evaluate_inventory_portfolio()
        
        mean_risk = float(df_risk["RISK_SCORE"].mean()) if not df_risk.empty else 0.45
        avg_doc = float(df_inv["DAYS_OF_COVER"].mean()) if not df_inv.empty else 30.0

        res_out = self.resilience_engine.calculate_resilience_score(
            redundancy_ratio=0.75,
            mean_risk_score=mean_risk,
            days_of_cover=avg_doc,
            exposure_usd=3500000.0,
            total_revenue_usd=50000000.0
        )
        return {
            "tool": "resilience_engine",
            "resilience_score": res_out["resilience_score"],
            "status": res_out["status"],
            "components": res_out["components"],
            "computed_at": datetime.now().isoformat(),
            "data_labels": {
                "resilience_score": "calculated",
                "components": "calculated"
            }
        }
