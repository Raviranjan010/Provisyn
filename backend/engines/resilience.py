"""Resilience Scoring Engine for PROVISYN.
Computes multi-dimensional Resilience Index [0.0 - 100.0] before and after simulated interventions.
Weighted across: Redundancy (25%), Risk Hedging (25%), Buffer Coverage (25%), and Exposure Containment (25%).
"""
from typing import Dict, Any, Optional
import pandas as pd
from backend.core.logging import get_logger
from backend.data.repository import BaseRepository

logger = get_logger(__name__)

class ResilienceEngine:
    """Engine computing composite supply chain resilience index."""

    def __init__(self, repo: BaseRepository):
        self.repo = repo

    def calculate_resilience_score(
        self,
        redundancy_ratio: float = 0.70,
        mean_risk_score: float = 0.45,
        days_of_cover: float = 30.0,
        exposure_usd: float = 2000000.0,
        total_revenue_usd: float = 100000000.0
    ) -> Dict[str, Any]:
        """Compute composite resilience score [0 - 100]."""
        # 1. Redundancy Component (0 - 25 pts)
        c_redundancy = max(0.0, min(25.0, redundancy_ratio * 25.0))

        # 2. Risk Hedging Component (0 - 25 pts, lower risk -> higher score)
        c_risk = max(0.0, min(25.0, (1.0 - mean_risk_score) * 25.0))

        # 3. Buffer Coverage Component (0 - 25 pts, 45d = 25 pts)
        c_buffer = max(0.0, min(25.0, (days_of_cover / 45.0) * 25.0))

        # 4. Exposure Containment Component (0 - 25 pts, lower exposure/revenue ratio -> higher score)
        ratio = exposure_usd / max(1.0, total_revenue_usd)
        c_exposure = max(0.0, min(25.0, (1.0 - min(1.0, ratio * 5.0)) * 25.0))

        composite = round(c_redundancy + c_risk + c_buffer + c_exposure, 1)

        return {
            "resilience_score": composite,
            "components": {
                "redundancy": round(c_redundancy, 1),
                "risk_hedging": round(c_risk, 1),
                "buffer_coverage": round(c_buffer, 1),
                "exposure_containment": round(c_exposure, 1),
            },
            "status": "STRONG" if composite >= 75.0 else ("ADEQUATE" if composite >= 55.0 else "VULNERABLE")
        }

    def evaluate_intervention(
        self,
        baseline_score: float,
        intervention_type: str,
        investment_cost: float
    ) -> Dict[str, Any]:
        """Calculate before/after resilience delta when an intervention is applied."""
        # Beneficial interventions increase resilience
        if intervention_type == "ADD_ALTERNATE_SUPPLIER":
            delta = 8.5
        elif intervention_type == "INCREASE_SAFETY_STOCK":
            delta = 6.0
        elif intervention_type == "REGIONAL_DUAL_SOURCING":
            delta = 11.0
        elif intervention_type == "EXPEDITE_CONTRACT":
            delta = 3.5
        else:
            delta = 2.0

        new_score = min(100.0, max(0.0, baseline_score + delta))
        return {
            "baseline_score": baseline_score,
            "new_score": new_score,
            "delta": delta,
            "investment_cost": investment_cost,
            "roi_ratio": round(delta / max(1.0, investment_cost / 10000.0), 2)
        }
