"""PROVISYN Copilot Agent.
Orchestrates decision intelligence tool calls with strict anti-hallucination grounding.
Every cited number is verified against tool outputs in the current turn.
"""
import re
from typing import Dict, List, Any, Optional, Tuple
from backend.core.logging import get_logger
from backend.data.repository import BaseRepository, get_repository
from backend.copilot.tools import CopilotToolRegistry

logger = get_logger(__name__)

class CopilotAgent:
    """Conversational Decision Intelligence Agent grounded in PROVISYN analytical engines."""

    def __init__(self, repo: Optional[BaseRepository] = None):
        self.repo = repo or get_repository()
        self.tools = CopilotToolRegistry(self.repo)

    def process_query(self, user_prompt: str) -> Dict[str, Any]:
        """Process user query, invoke required engine tool, and generate grounded response."""
        p_lower = user_prompt.lower()
        tool_name = None
        tool_output: Dict[str, Any] = {}
        narrative = ""
        structured_facts: List[Dict[str, str]] = []

        # 1. Check for entity risk queries (e.g. "Why is V10001 high risk?" or "risk score of Outback Lithium")
        vendor_match = re.search(r"\b(v\d{4,5})\b", p_lower)
        if ("risk" in p_lower or "why" in p_lower or "driver" in p_lower) and (vendor_match or "outback" in p_lower or "katanga" in p_lower or "supplier" in p_lower):
            entity_id = vendor_match.group(1).upper() if vendor_match else "V10001"
            if "outback" in p_lower:
                entity_id = "V10001"
            elif "katanga" in p_lower:
                entity_id = "V10003"

            tool_name = "risk_engine"
            tool_output = self.tools.tool_risk_query(entity_id)
            score = tool_output["risk_score"]
            cat = tool_output["risk_category"]
            name = tool_output["entity_name"]
            
            narrative = (
                f"**{name}** (`{entity_id}`) has an evaluated risk score of **{score:.4f}** "
                f"classified as **{cat}** risk."
            )
            structured_facts.append({"label": "Risk Score", "value": f"{score:.4f}", "source": "risk_engine"})
            structured_facts.append({"label": "Risk Category", "value": cat, "source": "risk_engine"})
            
            drivers_summary = []
            for d in tool_output.get("drivers", [])[:3]:
                drivers_summary.append(f"- **{d['factor']}**: {d['impact']} impact ({d['description']})")
            if drivers_summary:
                narrative += "\n\n**Key Risk Drivers (SHAP / Multi-Tier Attribution):**\n" + "\n".join(drivers_summary)

        # 2. Check for Single Points of Failure / Bottlenecks
        elif "spof" in p_lower or "bottleneck" in p_lower or "single point" in p_lower:
            tool_name = "graph_engine"
            tool_output = self.tools.tool_spof_bottlenecks(top_n=5)
            total = tool_output["total_bottlenecks"]
            narrative = f"Network topology and alternative-path analysis identified **{total} critical bottlenecks** in the supply network."
            structured_facts.append({"label": "Total Bottlenecks", "value": str(total), "source": "graph_engine"})
            
            b_list = []
            for b in tool_output.get("bottlenecks", [])[:3]:
                b_list.append(f"- **{b['entity_name']}** (`{b['entity_id']}`): {b['severity']} severity (PageRank: {b['pagerank']}, Redundancy Count: {b['redundancy_count']})")
            if b_list:
                narrative += "\n\n**Top Structural Bottlenecks:**\n" + "\n".join(b_list)

        # 3. Check for Financial Exposure / Revenue at Risk
        elif "revenue" in p_lower or "exposure" in p_lower or "dollar" in p_lower or "loss" in p_lower:
            tool_name = "financial_engine"
            seed = ["V10001"] if ("lithium" in p_lower or "v10001" in p_lower) else ["V10003"]
            tool_output = self.tools.tool_financial_exposure(seed_entities=seed, severity=0.85)
            rev = tool_output["revenue_at_risk_usd"]
            orders = tool_output["affected_orders_count"]
            exp = tool_output["total_financial_exposure_usd"]
            
            narrative = (
                f"Under an 85% disruption shock to `{seed[0]}`, projected **Revenue at Risk is ${rev:,.2f}** "
                f"across **{orders} impacted customer orders**, with total financial exposure estimated at **${exp:,.2f}**."
            )
            structured_facts.append({"label": "Revenue at Risk", "value": f"${rev:,.2f}", "source": "financial_engine"})
            structured_facts.append({"label": "Total Exposure", "value": f"${exp:,.2f}", "source": "financial_engine"})
            structured_facts.append({"label": "Impacted Orders", "value": str(orders), "source": "financial_engine"})

        # 4. Check for Cascade Disruption Simulation
        elif "cascade" in p_lower or "fail" in p_lower or "propagation" in p_lower or "what happens if" in p_lower:
            tool_name = "cascade_engine"
            seed = ["V10001"]
            tool_output = self.tools.tool_cascade_simulation(seed_entities=seed, severity=0.85)
            mats = tool_output["affected_materials_count"]
            facts = tool_output["affected_factories_count"]
            rev = tool_output["revenue_at_risk_usd"]
            
            narrative = (
                f"Cascade simulation traversing BOM and production links reveals that a disruption at `{seed[0]}` "
                f"propagates downstream across **{mats} materials** and compromises operations at **{facts} factories**, "
                f"placing **${rev:,.2f}** in order value at risk."
            )
            structured_facts.append({"label": "Affected Materials", "value": str(mats), "source": "cascade_engine"})
            structured_facts.append({"label": "Affected Factories", "value": str(facts), "source": "cascade_engine"})
            structured_facts.append({"label": "Downstream Revenue at Risk", "value": f"${rev:,.2f}", "source": "cascade_engine"})

        # 5. Check for Inventory / Stockout Risk
        elif "stockout" in p_lower or "inventory" in p_lower or "cover" in p_lower:
            tool_name = "inventory_engine"
            tool_output = self.tools.tool_inventory_stockout(top_n=5)
            items = tool_output.get("items", [])
            narrative = f"Inventory analysis evaluated **{len(items)} materials** with elevated stockout risk under dynamic supplier lead-time scaling."
            structured_facts.append({"label": "At-Risk SKUs", "value": str(len(items)), "source": "inventory_engine"})
            
            lines = []
            for it in items[:3]:
                lines.append(f"- **{it['description']}** (`{it['material_id']}`): {it['days_of_cover']} days of cover, Stockout Probability: {it['stockout_probability']:.2f}")
            if lines:
                narrative += "\n\n**Most Critical Inventory Depletions:**\n" + "\n".join(lines)

        # 6. Check for Optimization / Recommendations
        elif "recommend" in p_lower or "optimiz" in p_lower or "budget" in p_lower or "fund" in p_lower:
            tool_name = "optimization_engine"
            budget_match = re.search(r"(\d+[\d,.]*)", p_lower)
            budget = float(budget_match.group(1).replace(",", "")) if budget_match and float(budget_match.group(1).replace(",", "")) > 1000 else 500000.0
            tool_output = self.tools.tool_optimization_recommendations(budget_usd=budget)
            
            spend = tool_output["total_spend_usd"]
            gain = tool_output["resilience_gain"]
            exp_red = tool_output["exposure_reduction_usd"]
            num_actions = len(tool_output["selected_actions"])

            narrative = (
                f"Under a **${budget:,.0f}** capital budget, linear optimization selected **{num_actions} optimal actions** "
                f"committing **${spend:,.0f}**, achieving a projected **+{gain:.1f} pt** resilience gain and "
                f"reducing exposure by **${exp_red:,.0f}**."
            )
            structured_facts.append({"label": "Optimized Spend", "value": f"${spend:,.0f}", "source": "optimization_engine"})
            structured_facts.append({"label": "Resilience Gain", "value": f"+{gain:.1f} pts", "source": "optimization_engine"})
            structured_facts.append({"label": "Exposure Reduction", "value": f"${exp_red:,.0f}", "source": "optimization_engine"})

        # 7. Check for Resilience Assessment
        elif "resilience" in p_lower or "score" in p_lower or "posture" in p_lower:
            tool_name = "resilience_engine"
            tool_output = self.tools.tool_resilience_assessment()
            score = tool_output["resilience_score"]
            status = tool_output["status"]
            comps = tool_output["components"]

            narrative = f"Current portfolio resilience index is **{score} / 100** (**{status}** posture)."
            structured_facts.append({"label": "Composite Resilience", "value": f"{score} / 100", "source": "resilience_engine"})
            structured_facts.append({"label": "Risk Hedging", "value": f"{comps.get('risk_hedging', 0)} pts", "source": "resilience_engine"})
            structured_facts.append({"label": "Buffer Coverage", "value": f"{comps.get('buffer_coverage', 0)} pts", "source": "resilience_engine"})

        # 8. Unrecognized or Insufficient Data fallback per Part 25
        else:
            tool_name = "copilot_dispatcher"
            tool_output = {"status": "insufficient_context"}
            narrative = (
                "Insufficient specific parameters provided to formulate an engine query. "
                "You can ask about:\n"
                "- **Supplier Risk**: 'Why is V10001 high risk?'\n"
                "- **Bottlenecks**: 'What are our single points of failure?'\n"
                "- **Financial Exposure**: 'What is our revenue at risk under an Outback Lithium disruption?'\n"
                "- **Cascade Disruption**: 'What happens if Outback Lithium fails?'\n"
                "- **Inventory Stockouts**: 'Which materials are at stockout risk?'\n"
                "- **Prescriptive Optimization**: 'Given a $500,000 budget, what should we fund?'"
            )

        return {
            "query": user_prompt,
            "tool_called": tool_name,
            "tool_output": tool_output,
            "narrative": narrative,
            "structured_facts": structured_facts
        }
