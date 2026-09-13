"""Budget-Constrained Prescriptive Optimization Engine for PROVISYN.
Solves mixed-integer linear programming (MILP) allocation using PuLP.
Maximizes risk & exposure reduction subject to strict budget constraints.
Per decision_engines.md: Never fabricates solutions on infeasible constraints.
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import pulp
import pandas as pd
from backend.core.logging import get_logger
from backend.data.repository import BaseRepository

logger = get_logger(__name__)

@dataclass
class CandidateAction:
    action_id: str
    title: str
    action_type: str
    target_entity: str
    estimated_cost: float
    risk_reduction: float          # Points [0 - 100]
    exposure_reduction: float      # USD
    resilience_improvement: float  # Points [0 - 100]
    recovery_days_improvement: int
    confidence: float

@dataclass
class OptimizationResult:
    status: str
    is_feasible: bool
    budget_constraint: float
    total_spend: float
    total_exposure_reduction: float
    total_resilience_gain: float
    selected_actions: List[Dict[str, Any]]
    message: str

class OptimizationEngine:
    """Engine solving Knapsack / MILP budget allocation across candidate interventions."""

    DEFAULT_CANDIDATES: List[CandidateAction] = [
        CandidateAction(
            action_id="ACT-01",
            title="Dual-Source Battery Grade Lithium Carbonate",
            action_type="DUAL_SOURCING",
            target_entity="M-3002",
            estimated_cost=250000.0,
            risk_reduction=18.5,
            exposure_reduction=1250000.0,
            resilience_improvement=11.2,
            recovery_days_improvement=35,
            confidence=0.92
        ),
        CandidateAction(
            action_id="ACT-02",
            title="Expand Safety Stock Buffer for Electrolyte LiPF6",
            action_type="INCREASE_SAFETY_STOCK",
            target_entity="M-3012",
            estimated_cost=95000.0,
            risk_reduction=12.0,
            exposure_reduction=680000.0,
            resilience_improvement=7.5,
            recovery_days_improvement=21,
            confidence=0.95
        ),
        CandidateAction(
            action_id="ACT-03",
            title="Pre-qualify Backup Chilean Lithium Extractor",
            action_type="SUPPLIER_DIVERSIFICATION",
            target_entity="V10002",
            estimated_cost=180000.0,
            risk_reduction=15.0,
            exposure_reduction=950000.0,
            resilience_improvement=9.0,
            recovery_days_improvement=28,
            confidence=0.88
        ),
        CandidateAction(
            action_id="ACT-04",
            title="Contract Guaranteed Maritime Express Logistics Slot",
            action_type="EXPEDITE_CONTRACT",
            target_entity="SHP-PORT",
            estimated_cost=65000.0,
            risk_reduction=8.5,
            exposure_reduction=420000.0,
            resilience_improvement=4.5,
            recovery_days_improvement=14,
            confidence=0.85
        ),
        CandidateAction(
            action_id="ACT-05",
            title="Nearshore High-Voltage Harness Assembly to Mexico",
            action_type="REGIONAL_SOURCING",
            target_entity="M-2005",
            estimated_cost=320000.0,
            risk_reduction=22.0,
            exposure_reduction=1650000.0,
            resilience_improvement=13.0,
            recovery_days_improvement=42,
            confidence=0.90
        ),
        CandidateAction(
            action_id="ACT-06",
            title="Strategic Ingot Reserve Agreement for Cobalt Refiners",
            action_type="BUFFER_RESERVE",
            target_entity="M-3003",
            estimated_cost=150000.0,
            risk_reduction=14.0,
            exposure_reduction=820000.0,
            resilience_improvement=8.0,
            recovery_days_improvement=25,
            confidence=0.91
        ),
    ]

    def __init__(self, repo: BaseRepository):
        self.repo = repo

    def optimize_allocations(
        self,
        budget: float,
        candidate_actions: Optional[List[CandidateAction]] = None
    ) -> OptimizationResult:
        """Solve 0-1 Knapsack MILP via PuLP maximizing exposure & resilience reduction."""
        candidates = candidate_actions if candidate_actions is not None else self.DEFAULT_CANDIDATES
        
        # Infeasibility check per Part 18/25 honesty requirement
        if budget <= 0 or not candidates:
            return OptimizationResult(
                status="OPTIMIZATION_UNAVAILABLE",
                is_feasible=False,
                budget_constraint=budget,
                total_spend=0.0,
                total_exposure_reduction=0.0,
                total_resilience_gain=0.0,
                selected_actions=[],
                message="Optimization unavailable: Budget constraint is zero or no candidate actions provided."
            )

        min_cost = min(c.estimated_cost for c in candidates)
        if budget < min_cost:
            return OptimizationResult(
                status="OPTIMIZATION_UNAVAILABLE",
                is_feasible=False,
                budget_constraint=budget,
                total_spend=0.0,
                total_exposure_reduction=0.0,
                total_resilience_gain=0.0,
                selected_actions=[],
                message=f"Optimization unavailable: Budget ${budget:,.0f} is below minimum action cost ${min_cost:,.0f}."
            )

        # Build PuLP model
        prob = pulp.LpProblem("Supply_Chain_Risk_Mitigation_Allocation", pulp.LpMaximize)

        # Decision variables: x_i in {0, 1}
        x_vars = {c.action_id: pulp.LpVariable(f"x_{c.action_id}", cat="Binary") for c in candidates}

        # Objective: Maximize combined exposure and resilience reduction
        # Normalized objective: exposure ($) + resilience (pts * $50,000)
        prob += pulp.lpSum([
            (c.exposure_reduction + c.resilience_improvement * 50000.0) * x_vars[c.action_id]
            for c in candidates
        ])

        # Constraint: Budget
        prob += pulp.lpSum([
            c.estimated_cost * x_vars[c.action_id]
            for c in candidates
        ]) <= budget, "Budget_Constraint"

        # Solve (quietly without console spam)
        solver = pulp.PULP_CBC_CMD(msg=False)
        status_code = prob.solve(solver)

        if pulp.LpStatus[status_code] != "Optimal":
            return OptimizationResult(
                status="OPTIMIZATION_UNAVAILABLE",
                is_feasible=False,
                budget_constraint=budget,
                total_spend=0.0,
                total_exposure_reduction=0.0,
                total_resilience_gain=0.0,
                selected_actions=[],
                message="Optimization unavailable: Solver failed to find an optimal feasible allocation."
            )

        # Extract selected actions
        selected = []
        total_spend = 0.0
        total_exp_red = 0.0
        total_res_gain = 0.0

        for c in candidates:
            if pulp.value(x_vars[c.action_id]) == 1.0:
                selected.append({
                    "action_id": c.action_id,
                    "title": c.title,
                    "action_type": c.action_type,
                    "target_entity": c.target_entity,
                    "estimated_cost": c.estimated_cost,
                    "risk_reduction": c.risk_reduction,
                    "exposure_reduction": c.exposure_reduction,
                    "resilience_improvement": c.resilience_improvement,
                    "recovery_days_improvement": c.recovery_days_improvement,
                    "confidence": c.confidence,
                    "roi_ratio": round(c.exposure_reduction / max(1.0, c.estimated_cost), 2)
                })
                total_spend += c.estimated_cost
                total_exp_red += c.exposure_reduction
                total_res_gain += c.resilience_improvement

        # Sort selected actions by ROI descending
        selected.sort(key=lambda x: x["roi_ratio"], reverse=True)
        for idx, act in enumerate(selected):
            act["rank"] = idx + 1

        return OptimizationResult(
            status="OPTIMAL",
            is_feasible=True,
            budget_constraint=budget,
            total_spend=round(total_spend, 2),
            total_exposure_reduction=round(total_exp_red, 2),
            total_resilience_gain=round(total_res_gain, 1),
            selected_actions=selected,
            message="Optimal feasible mitigation allocation determined."
        )
