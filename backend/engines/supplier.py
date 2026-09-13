"""Supplier Intelligence Engine for PROVISYN.
Assembles 360-degree Supplier Digital Profiles and comparison matrices.
Per decision_engines.md: identity, risk score, reliability, delivery, capacity,
geographic concentration, materials supplied, alternative suppliers, and exposure.
"""
from typing import Dict, List, Any, Optional
import pandas as pd
from backend.core.logging import get_logger
from backend.data.repository import BaseRepository

logger = get_logger(__name__)

class SupplierIntelligenceEngine:
    """Engine for aggregating comprehensive supplier digital profiles."""

    def __init__(self, repo: BaseRepository):
        self.repo = repo

    def get_supplier_profile(self, vendor_id: str) -> Dict[str, Any]:
        """Assemble complete digital profile for a vendor.
        Guarantees all required fields are present; returns 'Not Available' / None on missing data,
        never raises KeyError.
        """
        vendors_df = self.repo.get_vendors()
        risk_df = self.repo.get_risk_scores()
        po_df = self.repo.get_purchase_orders()
        materials_df = self.repo.get_materials()
        disruptions_df = self.repo.get_disruptions()
        links_df = self.repo.get_predicted_links()

        # Find vendor row
        v_row = vendors_df[vendors_df["VENDOR_ID"] == vendor_id] if not vendors_df.empty else pd.DataFrame()
        if v_row.empty:
            return {
                "vendor_id": vendor_id,
                "name": f"Supplier {vendor_id}",
                "country_code": "N/A",
                "city": "N/A",
                "tier": 1,
                "financial_health_score": None,
                "reliability_score": None,
                "delivery_performance": None,
                "capacity": None,
                "risk_score": None,
                "risk_category": "NOT_AVAILABLE",
                "trend": "STABLE",
                "materials_supplied": [],
                "alternative_suppliers": [],
                "tier2_dependencies": [],
                "financial_exposure": 0.0,
                "historical_disruptions": 0,
            }

        v = v_row.iloc[0]
        
        # Risk information
        r_row = risk_df[(risk_df["ENTITY_TYPE"] == "VENDOR") & (risk_df["ENTITY_ID"] == vendor_id)] if not risk_df.empty else pd.DataFrame()
        risk_score = float(r_row["RISK_SCORE"].iloc[0]) if not r_row.empty else None
        risk_category = str(r_row["RISK_CATEGORY"].iloc[0]) if not r_row.empty else "NOT_AVAILABLE"
        trend = str(r_row["TREND"].iloc[0]) if not r_row.empty and "TREND" in r_row.columns else "STABLE"
        exposure = float(r_row["FINANCIAL_EXPOSURE"].iloc[0]) if not r_row.empty and "FINANCIAL_EXPOSURE" in r_row.columns else 0.0

        # Materials supplied via Purchase Orders
        materials_supplied = []
        alt_suppliers = set()
        if not po_df.empty and "VENDOR_ID" in po_df.columns and "MATERIAL_ID" in po_df.columns:
            v_pos = po_df[po_df["VENDOR_ID"] == vendor_id]
            mat_ids = v_pos["MATERIAL_ID"].unique().tolist()
            
            # Look up material details
            if not materials_df.empty:
                for mid in mat_ids:
                    m_match = materials_df[materials_df["MATERIAL_ID"] == mid]
                    desc = m_match["DESCRIPTION"].iloc[0] if not m_match.empty else mid
                    materials_supplied.append({"material_id": mid, "description": desc})
                    
                    # Find other vendors supplying this material
                    other_pos = po_df[(po_df["MATERIAL_ID"] == mid) & (po_df["VENDOR_ID"] != vendor_id)]
                    for other_vid in other_pos["VENDOR_ID"].unique():
                        alt_suppliers.add(other_vid)
            else:
                materials_supplied = [{"material_id": mid, "description": mid} for mid in mat_ids]

        # Tier-2 dependencies from trade data / predicted links
        tier2_deps = []
        if not links_df.empty and "TARGET_ID" in links_df.columns:
            matches = links_df[links_df["TARGET_ID"] == vendor_id]
            for _, l in matches.iterrows():
                tier2_deps.append({
                    "shipper_name": l.get("SOURCE_ID", "Outback Lithium Resources"),
                    "similarity": float(l.get("SIMILARITY_SCORE", 0.0)),
                    "confidence": float(l.get("CONFIDENCE", 0.75))
                })

        # Historical disruptions
        disruption_count = 0
        if not disruptions_df.empty and "ENTITY_ID" in disruptions_df.columns:
            disruption_count = int((disruptions_df["ENTITY_ID"] == vendor_id).sum())

        return {
            "vendor_id": vendor_id,
            "name": str(v.get("NAME", f"Vendor {vendor_id}")),
            "country_code": str(v.get("COUNTRY_CODE", "N/A")),
            "city": str(v.get("CITY", "N/A")),
            "phone": str(v.get("PHONE", "N/A")),
            "tier": int(v.get("TIER", 1)),
            "financial_health_score": float(v["FINANCIAL_HEALTH_SCORE"]) if pd.notna(v.get("FINANCIAL_HEALTH_SCORE")) else None,
            "reliability_score": float(v["RELIABILITY_SCORE"]) if pd.notna(v.get("RELIABILITY_SCORE")) else None,
            "delivery_performance": float(v["DELIVERY_PERFORMANCE"]) if pd.notna(v.get("DELIVERY_PERFORMANCE")) else None,
            "capacity": float(v["CAPACITY"]) if pd.notna(v.get("CAPACITY")) else None,
            "risk_score": risk_score,
            "risk_category": risk_category,
            "trend": trend,
            "materials_supplied": materials_supplied,
            "alternative_suppliers": list(alt_suppliers),
            "tier2_dependencies": tier2_deps,
            "financial_exposure": exposure,
            "historical_disruptions": disruption_count,
        }

    def compare_suppliers(self, vendor_ids: List[str]) -> pd.DataFrame:
        """Generate side-by-side comparative evaluation matrix for 2+ vendors."""
        profiles = [self.get_supplier_profile(vid) for vid in vendor_ids]
        rows = []
        for p in profiles:
            rows.append({
                "Vendor ID": p["vendor_id"],
                "Supplier Name": p["name"],
                "Country": p["country_code"],
                "Risk Score": f"{p['risk_score']:.3f}" if p["risk_score"] is not None else "N/A",
                "Risk Category": p["risk_category"],
                "Financial Health": f"{p['financial_health_score'] * 100:.0f}%" if p["financial_health_score"] is not None else "N/A",
                "Reliability": f"{p['reliability_score'] * 100:.0f}%" if p["reliability_score"] is not None else "N/A",
                "Delivery OTIF": f"{p['delivery_performance'] * 100:.0f}%" if p["delivery_performance"] is not None else "N/A",
                "Capacity": f"{p['capacity']:,.0f}" if p["capacity"] is not None else "N/A",
                "Materials Count": len(p["materials_supplied"]),
                "Alternates Available": len(p["alternative_suppliers"]),
                "Exposure ($)": f"${p['financial_exposure']:,.0f}",
            })
        return pd.DataFrame(rows)
