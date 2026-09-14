"""SHAP-based Explainable AI (XAI) for Supply Chain Risk.
Decomposes tabular model risk scores into quantifiable feature contribution drivers.
"""
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from backend.core.logging import get_logger
from ml.risk.model import FEATURE_NAMES, TabularRiskPipeline

logger = get_logger(__name__)

class RiskModelExplainer:
    """SHAP explainer for tabular risk predictions."""

    def __init__(self, pipeline: TabularRiskPipeline):
        self.pipeline = pipeline
        self.feature_names = pipeline.feature_names
        self._explainer = None
        self._init_shap()

    def _init_shap(self):
        """Initialize SHAP TreeExplainer with graceful fallback if shap library encounters issues."""
        try:
            import shap
            if hasattr(self.pipeline, "regressor") and self.pipeline.is_trained:
                self._explainer = shap.TreeExplainer(self.pipeline.regressor)
                logger.info("Initialized SHAP TreeExplainer successfully.")
        except Exception as e:
            logger.warning(f"SHAP initialization fallback: {e}")
            self._explainer = None

    def explain_instance(self, feature_row: pd.Series) -> List[Dict[str, Any]]:
        """Explain a single entity feature row, returning ordered feature contribution drivers."""
        X_vec = np.array([feature_row[f] for f in self.feature_names]).reshape(1, -1)

        feature_display_names = {
            "financial_health_score": "Financial Health & Solvency",
            "reliability_score": "Contractual Reliability",
            "delivery_performance": "Historical On-Time Delivery",
            "tier": "Supply Chain Tier Depth",
            "capacity_norm": "Production Capacity Volume",
            "regional_base_risk": "Regional Operating Baseline",
            "regional_geopolitical_risk": "Geopolitical Transit Risk",
            "pagerank_score": "Network PageRank Centrality",
            "betweenness_score": "Bottleneck Betweenness",
            "material_criticality_avg": "Downstream Material Criticality",
        }

        if self._explainer is not None:
            try:
                shap_values = self._explainer.shap_values(X_vec)
                vals = shap_values[0]
                drivers = []
                for idx, fname in enumerate(self.feature_names):
                    impact_val = float(vals[idx])
                    sign = "+" if impact_val >= 0 else ""
                    drivers.append({
                        "factor": feature_display_names.get(fname, fname),
                        "raw_feature": fname,
                        "value": round(float(feature_row[fname]), 3),
                        "shap_value": round(impact_val, 4),
                        "impact": f"{sign}{impact_val:.2f}",
                        "description": f"Feature value {round(float(feature_row[fname]), 2)} contributed {sign}{impact_val:.2f} pts"
                    })
                # Sort by absolute impact descending
                drivers.sort(key=lambda d: abs(d["shap_value"]), reverse=True)
                return drivers
            except Exception as e:
                logger.warning(f"Error computing SHAP values: {e}, falling back to model feature importances")

        # Fallback to feature importance-weighted heuristic if SHAP tree explainer fails
        drivers = []
        importances = getattr(self.pipeline.regressor, "feature_importances_", [0.1]*len(self.feature_names))
        for idx, fname in enumerate(self.feature_names):
            val = float(feature_row[fname])
            imp = float(importances[idx])
            contrib = (val - 0.5) * imp
            sign = "+" if contrib >= 0 else ""
            drivers.append({
                "factor": feature_display_names.get(fname, fname),
                "raw_feature": fname,
                "value": round(val, 3),
                "shap_value": round(contrib, 4),
                "impact": f"{sign}{contrib:.2f}",
                "description": f"Weighted model contribution ({sign}{contrib:.2f})"
            })
        drivers.sort(key=lambda d: abs(d["shap_value"]), reverse=True)
        return drivers
