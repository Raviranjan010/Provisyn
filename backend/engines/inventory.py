"""Inventory and Demand Intelligence Engine for PROVISYN.
Computes risk-aware safety stock, days of cover, reorder points, and stockout probability.
Per decision_engines.md: Safety stock is dynamically scaled by supplier risk score:
safety_stock = base_safety_stock * (1 + risk_score * k).
"""
import math
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from backend.core.logging import get_logger
from backend.data.repository import BaseRepository

logger = get_logger(__name__)

@dataclass
class InventoryItemMetrics:
    material_id: str
    description: str
    factory_id: str
    on_hand_qty: float
    avg_daily_demand: float
    lead_time_days: int
    supplier_risk_score: float
    days_of_cover: float
    base_safety_stock: float
    risk_aware_safety_stock: float
    reorder_point: float
    stockout_probability: float
    stockout_risk_level: str

class InventoryEngine:
    """Engine for risk-aware inventory replenishment and stockout risk forecasting."""

    # Disclosed constant scaling supplier risk into buffer inventory requirements
    SAFETY_STOCK_RISK_MULTIPLIER = 0.50

    def __init__(self, repo: BaseRepository):
        self.repo = repo

    def calculate_days_of_cover(self, on_hand: float, daily_demand: float) -> float:
        """Calculate days of cover with zero-demand safety."""
        if daily_demand <= 0:
            return 999.0 if on_hand > 0 else 0.0
        return max(0.0, on_hand / daily_demand)

    def calculate_risk_aware_safety_stock(self, base_safety_stock: float, risk_score: float) -> float:
        """Calculate dynamic safety stock scaled by upstream supplier risk."""
        bounded_risk = max(0.0, min(1.0, risk_score))
        return base_safety_stock * (1.0 + bounded_risk * self.SAFETY_STOCK_RISK_MULTIPLIER)

    def calculate_reorder_point(self, daily_demand: float, lead_time_days: int, safety_stock: float) -> float:
        """Calculate replenishment reorder point (ROP)."""
        return max(0.0, (daily_demand * lead_time_days) + safety_stock)

    def predict_stockout_probability(
        self,
        days_of_cover: float,
        lead_time_days: int,
        supplier_risk_score: float,
        demand_growth_rate: float = 0.10
    ) -> float:
        """Compute bounded stockout probability [0.0, 1.0].
        Logistic sigmoid function over replenishment risk ratio.
        Never produces negative or NaN values even on extremely high demand inputs.
        """
        if math.isnan(days_of_cover) or days_of_cover < 0:
            days_of_cover = 0.0
        
        bounded_risk = max(0.0, min(1.0, supplier_risk_score))
        effective_lead_time = lead_time_days * (1.0 + bounded_risk * 0.5)

        # Coverage ratio: days of cover relative to lead time
        # If coverage is much less than lead time -> high stockout risk
        # Avoid zero division
        ratio = days_of_cover / max(1.0, float(effective_lead_time))
        
        # Logit: z = (1.0 - ratio) * 3.0 + bounded_risk * 2.0 + demand_growth_rate * 2.0
        z = (1.0 - ratio) * 2.5 + bounded_risk * 1.5 + (demand_growth_rate * 1.2)
        
        # Sigmoid with overflow clamp
        z_clamped = max(-20.0, min(20.0, z))
        prob = 1.0 / (1.0 + math.exp(-z_clamped))
        return float(max(0.0, min(1.0, prob)))

    def evaluate_inventory_portfolio(self) -> pd.DataFrame:
        """Evaluate inventory metrics across all materials and factories."""
        inventory_df = self.repo.get_inventory()
        materials_df = self.repo.get_materials()
        risk_df = self.repo.get_risk_scores()
        po_df = self.repo.get_purchase_orders()

        if inventory_df.empty or materials_df.empty:
            return pd.DataFrame()

        # Build material risk map
        mat_risk_map = {}
        if not risk_df.empty:
            for _, r in risk_df.iterrows():
                if r["ENTITY_TYPE"] == "MATERIAL":
                    mat_risk_map[str(r["ENTITY_ID"])] = float(r.get("RISK_SCORE", 0.5))

        # Supplier risk map for materials via POs
        supplier_risk_map = {}
        if not risk_df.empty:
            for _, r in risk_df.iterrows():
                if r["ENTITY_TYPE"] == "VENDOR":
                    supplier_risk_map[str(r["ENTITY_ID"])] = float(r.get("RISK_SCORE", 0.5))

        mat_lead_map = dict(zip(materials_df["MATERIAL_ID"], materials_df.get("LEAD_TIME_DAYS", [21]*len(materials_df))))
        mat_desc_map = dict(zip(materials_df["MATERIAL_ID"], materials_df["DESCRIPTION"]))

        records = []
        for _, inv in inventory_df.iterrows():
            mid = str(inv["MATERIAL_ID"])
            fid = str(inv["FACTORY_ID"])
            on_hand = float(inv.get("ON_HAND_QTY", 500.0))
            base_safety = float(inv.get("SAFETY_STOCK", 300.0))
            
            # Approximate daily demand from safety stock
            lead_time = int(mat_lead_map.get(mid, 21))
            daily_demand = max(5.0, base_safety / 15.0)

            risk_score = mat_risk_map.get(mid, 0.45)
            doc = self.calculate_days_of_cover(on_hand, daily_demand)
            risk_aware_safety = self.calculate_risk_aware_safety_stock(base_safety, risk_score)
            rop = self.calculate_reorder_point(daily_demand, lead_time, risk_aware_safety)
            stockout_prob = self.predict_stockout_probability(doc, lead_time, risk_score)

            if stockout_prob >= 0.70:
                level = "CRITICAL"
            elif stockout_prob >= 0.45:
                level = "HIGH"
            elif stockout_prob >= 0.25:
                level = "WARNING"
            else:
                level = "HEALTHY"

            records.append({
                "MATERIAL_ID": mid,
                "DESCRIPTION": mat_desc_map.get(mid, mid),
                "FACTORY_ID": fid,
                "ON_HAND_QTY": round(on_hand, 1),
                "DAILY_DEMAND": round(daily_demand, 1),
                "LEAD_TIME_DAYS": lead_time,
                "SUPPLIER_RISK": round(risk_score, 3),
                "DAYS_OF_COVER": round(doc, 1),
                "BASE_SAFETY_STOCK": round(base_safety, 1),
                "RISK_AWARE_SAFETY_STOCK": round(risk_aware_safety, 1),
                "REORDER_POINT": round(rop, 1),
                "STOCKOUT_PROBABILITY": round(stockout_prob, 3),
                "STOCKOUT_RISK_LEVEL": level
            })

        df_out = pd.DataFrame(records)
        return df_out.sort_values(by="STOCKOUT_PROBABILITY", ascending=False)
