"""Prescriptive Recommendations Engine for PROVISYN.
Ranks, prioritizes, and formats mitigation interventions backed by the Optimization Engine.
Replaces static recommendations with mathematically optimal action plans.
"""
from typing import Dict, List, Any, Optional
import pandas as pd
from backend.core.logging import get_logger
from backend.data.repository import BaseRepository
from backend.engines.optimization import OptimizationEngine, CandidateAction, OptimizationResult

logger = get_logger(__name__)

class RecommendationEngine:
    """Engine synthesizing optimization outputs into prioritized prescriptive action portfolios."""

    def __init__(self, repo: BaseRepository):
        self.repo = repo
        self.opt_engine = OptimizationEngine(repo)

    def generate_recommendations(self, budget: float = 500000.0) -> Dict[str, Any]:
        """Generate ranked mitigation recommendations under available capital budget."""
        opt_res: OptimizationResult = self.opt_engine.optimize_allocations(budget=budget)

        if not opt_res.is_feasible:
            return {
                "status": opt_res.status,
                "is_feasible": False,
                "message": opt_res.message,
                "recommendations": [],
                "total_spend": 0.0,
                "exposure_reduction": 0.0,
                "resilience_gain": 0.0
            }

        # Persist to RECOMMENDATIONS table
        rec_records = []
        for a in opt_res.selected_actions:
            rec_records.append({
                "RECOMMENDATION_ID": a["action_id"],
                "SCENARIO_ID": "PORTFOLIO_MITIGATION",
                "TITLE": a["title"],
                "ACTION_TYPE": a["action_type"],
                "TARGET_ENTITY": a["target_entity"],
                "ESTIMATED_COST": a["estimated_cost"],
                "RISK_REDUCTION": a["risk_reduction"],
                "EXPOSURE_REDUCTION": a["exposure_reduction"],
                "RESILIENCE_IMPROVEMENT": a["resilience_improvement"],
                "RECOVERY_IMPROVEMENT": float(a["recovery_days_improvement"]),
                "CONFIDENCE": a["confidence"],
                "RANK": a["rank"]
            })

        if rec_records:
            df_recs = pd.DataFrame(rec_records)
            self.repo.write_table(df_recs, "RECOMMENDATIONS", overwrite=True)

        return {
            "status": "OPTIMAL",
            "is_feasible": True,
            "message": opt_res.message,
            "budget": budget,
            "total_spend": opt_res.total_spend,
            "exposure_reduction": opt_res.total_exposure_reduction,
            "resilience_gain": opt_res.total_resilience_gain,
            "recommendations": opt_res.selected_actions
        }
