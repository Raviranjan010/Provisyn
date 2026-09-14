"""Synthetic data generator for PROVISYN.
Ported from Snowflake Snowpark procedure GENERATE_SYNTHETIC_DATA (scripts/setup_networkx.sql).
Generates realistic EV battery supply chain data including:
- VENDORS, MATERIALS, PURCHASE_ORDERS, BILL_OF_MATERIALS, TRADE_DATA, REGIONS
- PRODUCTS, FACTORIES, ORDERS, INVENTORY, SHIPMENTS
- ALERTS, SCENARIOS, DISRUPTIONS, MODEL_VERSIONS
Embeds the synthetic 'Outback Lithium Resources' Tier-2 bottleneck scenario.
"""
import random
from datetime import datetime, timedelta
from typing import Dict
import pandas as pd
from backend.core.logging import get_logger
from backend.data.repository import BaseRepository

logger = get_logger(__name__)

REGIONS_CFG = {
    "CHN": {"name": "China", "weight": 0.15, "cities": ["Shanghai", "Shenzhen", "Beijing", "Guangzhou"]},
    "KOR": {"name": "South Korea", "weight": 0.15, "cities": ["Seoul", "Busan", "Ulsan", "Daegu"]},
    "JPN": {"name": "Japan", "weight": 0.10, "cities": ["Tokyo", "Osaka", "Nagoya", "Yokohama"]},
    "USA": {"name": "United States", "weight": 0.20, "cities": ["Charlotte", "Detroit", "Houston", "Phoenix"]},
    "MEX": {"name": "Mexico", "weight": 0.10, "cities": ["Monterrey", "Mexico City", "Guadalajara", "Tijuana"]},
    "DEU": {"name": "Germany", "weight": 0.10, "cities": ["Munich", "Stuttgart", "Frankfurt", "Berlin"]},
    "CHL": {"name": "Chile", "weight": 0.10, "cities": ["Santiago", "Antofagasta", "Valparaiso", "Concepcion"]},
    "AUS": {"name": "Australia", "weight": 0.05, "cities": ["Perth", "Sydney", "Melbourne", "Brisbane"]},
    "COD": {"name": "DR Congo", "weight": 0.05, "cities": ["Lubumbashi", "Kolwezi", "Kinshasa", "Likasi"]},
}

REGION_RISKS = {
    "CHN": {"base": 0.3, "geopolitical": 0.5, "natural": 0.2, "infrastructure": 0.7},
    "KOR": {"base": 0.2, "geopolitical": 0.3, "natural": 0.3, "infrastructure": 0.9},
    "JPN": {"base": 0.2, "geopolitical": 0.1, "natural": 0.5, "infrastructure": 0.95},
    "USA": {"base": 0.1, "geopolitical": 0.1, "natural": 0.2, "infrastructure": 0.9},
    "MEX": {"base": 0.3, "geopolitical": 0.2, "natural": 0.3, "infrastructure": 0.6},
    "DEU": {"base": 0.1, "geopolitical": 0.1, "natural": 0.1, "infrastructure": 0.95},
    "CHL": {"base": 0.4, "geopolitical": 0.2, "natural": 0.6, "infrastructure": 0.7},
    "AUS": {"base": 0.80, "geopolitical": 0.85, "natural": 0.85, "infrastructure": 0.45},
    "COD": {"base": 0.7, "geopolitical": 0.8, "natural": 0.3, "infrastructure": 0.3},
}

HS_CODES = {
    "2836.91": "Lithium Carbonate", "2825.20": "Lithium Hydroxide",
    "8106.00": "Cobalt and Cobalt Products", "7408.11": "Copper Wire",
    "7409.11": "Copper Plates", "8507.60": "Lithium-ion Batteries",
    "8541.40": "Semiconductor Devices", "3904.10": "PVC Compounds",
    "7601.10": "Aluminum Unwrought",
}

def generate_all_data(seed: int = 42) -> Dict[str, pd.DataFrame]:
    """Generate complete synthetic dataset."""
    random.seed(seed)
    
    # 1. Regions
    regions_data = []
    for code, risks in REGION_RISKS.items():
        regions_data.append({
            "REGION_CODE": code,
            "REGION_NAME": REGIONS_CFG[code]["name"],
            "BASE_RISK_SCORE": risks["base"],
            "GEOPOLITICAL_RISK": risks["geopolitical"],
            "NATURAL_DISASTER_RISK": risks["natural"],
            "INFRASTRUCTURE_SCORE": risks["infrastructure"],
            "UPDATED_AT": datetime.now()
        })
    df_regions = pd.DataFrame(regions_data)

    # 2. Vendors
    company_templates = {
        "battery": ["Seohan Battery Corp", "Hanyang Energy Solutions", "Jiaxing Battery Tech",
                     "Shenzhen Power Battery", "Kanto Energy Systems", "Chungnam Battery Works",
                     "Wuxi Energy Storage", "Nanjing Battery Group", "Hokkaido Energy Corp",
                     "Gyeonggi Battery Co.", "Fujian Energy Tech", "Daejeon Battery Systems"],
        "lithium": ["Appalachian Lithium Corp", "Atacama Resources Ltd", "Clearwater Lithium Inc",
                     "Kunlun Lithium Holdings", "Sichuan Lithium Works", "Goldfields Lithium Mining",
                     "Andean Minerals Ltd", "Cerrado Lithium Corp"],
        "cobalt": ["Lualaba Cobalt Mining", "Rhine Metals Refining", "Cascadia Cobalt Corp",
                    "Katavi Resources SPRL", "Great Rift Mining Co.", "Kolwezi Minerals Ltd"],
        "copper": ["Pacifica Copper Corp", "Cordillera Mining Ltd", "Outback Copper Holdings",
                    "Sonora Copper Works", "Andes Copper PLC", "Cariboo Copper Mining"],
        "electronics": ["Meridian Semiconductor", "Northgate Chip Technologies", "Pinnacle Microelectronics",
                         "Lakeshore Semiconductors", "Cascade Electronics Corp", "Summit Silicon Systems"],
        "materials": ["Rhine Chemical Works", "Kyushu Advanced Materials", "Honshu Chemical Corp",
                       "Saarland Specialty Chemicals", "Lakeside Advanced Materials", "Tidewater Polymer Corp"],
        "generic": ["Alpha Industries", "Beta Components", "Gamma Manufacturing",
                     "Delta Materials", "Epsilon Tech", "Zeta Precision", "Theta Systems"],
    }
    phone_prefixes = {"CHN":"+86","KOR":"+82","JPN":"+81","USA":"+1","MEX":"+52","DEU":"+49","CHL":"+56","AUS":"+61","COD":"+243"}
    region_codes = list(REGIONS_CFG.keys())
    region_weights = [REGIONS_CFG[r]["weight"] for r in region_codes]

    vendors_data = []
    used_names = set()
    for i in range(50):
        region = random.choices(region_codes, weights=region_weights, k=1)[0]
        city = random.choice(REGIONS_CFG[region]["cities"])
        if region in ["CHL","AUS"] and random.random() < 0.6: category = "lithium"
        elif region == "COD" and random.random() < 0.7: category = "cobalt"
        elif region in ["KOR","CHN","JPN"] and random.random() < 0.4: category = "battery"
        elif region in ["USA","DEU"] and random.random() < 0.3: category = "electronics"
        else: category = random.choice(["materials","generic","copper"])
        
        available = [n for n in company_templates.get(category, company_templates["generic"]) if n not in used_names]
        name = random.choice(available) if available else f"{category.title()} Corp {i+1}"
        used_names.add(name)
        phone = f"{phone_prefixes[region]}-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"
        
        vendors_data.append({
            "VENDOR_ID": f"V{10001+i}",
            "NAME": name,
            "COUNTRY_CODE": region,
            "CITY": city,
            "PHONE": phone,
            "TIER": 1,
            "FINANCIAL_HEALTH_SCORE": round(random.uniform(0.3, 0.95), 2),
            "RELIABILITY_SCORE": round(random.uniform(0.7, 0.98), 2),
            "DELIVERY_PERFORMANCE": round(random.uniform(0.75, 0.99), 2),
            "CAPACITY": float(random.randint(500, 5000)),
            "CREATED_AT": datetime.now(),
            "UPDATED_AT": datetime.now()
        })
    df_vendors = pd.DataFrame(vendors_data)

    # 3. Materials + BOM
    finished = [{"id":"M-1000","desc":"EV Battery Pack 85kWh","group":"FIN","unit":"PC","crit":1.0, "cost": 6500.0, "lead": 14}]
    semi = [
        {"id":"M-2001","desc":"Battery Module 400V","group":"SEMI","unit":"PC","crit":0.95, "cost": 950.0, "lead": 21},
        {"id":"M-2002","desc":"Battery Management System","group":"SEMI","unit":"PC","crit":0.9, "cost": 420.0, "lead": 28},
        {"id":"M-2003","desc":"Thermal Management Assembly","group":"SEMI","unit":"PC","crit":0.85, "cost": 310.0, "lead": 18},
        {"id":"M-2004","desc":"Battery Enclosure Assembly","group":"SEMI","unit":"PC","crit":0.8, "cost": 250.0, "lead": 14},
        {"id":"M-2005","desc":"High-Voltage Harness","group":"SEMI","unit":"PC","crit":0.85, "cost": 180.0, "lead": 14},
    ]
    raw = [
        {"id":"M-3001","desc":"Lithium Hydroxide Grade A","group":"RAW","unit":"KG","crit":0.95, "cost": 45.0, "lead": 45},
        {"id":"M-3002","desc":"Lithium Carbonate Battery Grade","group":"RAW","unit":"KG","crit":0.95, "cost": 38.0, "lead": 40},
        {"id":"M-3003","desc":"Cobalt Oxide Powder","group":"RAW","unit":"KG","crit":0.9, "cost": 62.0, "lead": 55},
        {"id":"M-3004","desc":"Nickel Sulfate Battery Grade","group":"RAW","unit":"KG","crit":0.85, "cost": 28.0, "lead": 35},
        {"id":"M-3005","desc":"Manganese Dioxide","group":"RAW","unit":"KG","crit":0.75, "cost": 14.0, "lead": 25},
        {"id":"M-3006","desc":"Synthetic Graphite Anode","group":"RAW","unit":"KG","crit":0.85, "cost": 19.0, "lead": 30},
        {"id":"M-3007","desc":"Silicon Anode Additive","group":"RAW","unit":"KG","crit":0.7, "cost": 32.0, "lead": 28},
        {"id":"M-3008","desc":"Copper Foil 8 Micron","group":"RAW","unit":"KG","crit":0.85, "cost": 22.0, "lead": 21},
        {"id":"M-3009","desc":"Copper Busbar 5mm","group":"RAW","unit":"KG","crit":0.8, "cost": 18.0, "lead": 21},
        {"id":"M-3010","desc":"Aluminum Foil 15 Micron","group":"RAW","unit":"KG","crit":0.8, "cost": 12.0, "lead": 18},
        {"id":"M-3011","desc":"Aluminum Housing Profile","group":"RAW","unit":"KG","crit":0.7, "cost": 15.0, "lead": 14},
        {"id":"M-3012","desc":"Electrolyte LiPF6 Solution","group":"RAW","unit":"L","crit":0.9, "cost": 55.0, "lead": 35},
        {"id":"M-3013","desc":"Ceramic Coated Separator","group":"RAW","unit":"M2","crit":0.9, "cost": 8.5, "lead": 30},
        {"id":"M-3014","desc":"BMS Controller IC","group":"RAW","unit":"PC","crit":0.85, "cost": 42.0, "lead": 60},
        {"id":"M-3015","desc":"Cell Monitoring ASIC","group":"RAW","unit":"PC","crit":0.85, "cost": 24.0, "lead": 60},
        {"id":"M-3016","desc":"Power MOSFET Module","group":"RAW","unit":"PC","crit":0.8, "cost": 16.0, "lead": 45},
        {"id":"M-3017","desc":"Thermal Interface Material","group":"RAW","unit":"KG","crit":0.75, "cost": 35.0, "lead": 21},
        {"id":"M-3018","desc":"Cooling Plate Aluminum","group":"RAW","unit":"PC","crit":0.7, "cost": 85.0, "lead": 28},
        {"id":"M-3019","desc":"High-Voltage Cable 35mm2","group":"RAW","unit":"M","crit":0.8, "cost": 18.0, "lead": 14},
        {"id":"M-3020","desc":"Connector Assembly HV","group":"RAW","unit":"PC","crit":0.75, "cost": 34.0, "lead": 21},
    ]
    materials_data = []
    for m in finished + semi + raw:
        materials_data.append({
            "MATERIAL_ID": m["id"],
            "DESCRIPTION": m["desc"],
            "MATERIAL_GROUP": m["group"],
            "UNIT_OF_MEASURE": m["unit"],
            "CRITICALITY_SCORE": m["crit"],
            "INVENTORY_DAYS": random.randint(15, 60),
            "UNIT_COST": m["cost"],
            "LEAD_TIME_DAYS": m["lead"],
            "CREATED_AT": datetime.now(),
            "UPDATED_AT": datetime.now()
        })
    df_materials = pd.DataFrame(materials_data)

    bom_data = []
    bom_id = 1
    for s in semi:
        bom_data.append({
            "BOM_ID": f"BOM-{bom_id:04d}",
            "PARENT_MATERIAL_ID": "M-1000",
            "CHILD_MATERIAL_ID": s["id"],
            "QUANTITY_PER_UNIT": float(random.randint(1,4)),
            "CREATED_AT": datetime.now()
        })
        bom_id += 1
    
    semi_to_raw = {
        "M-2001": ["M-3001","M-3002","M-3003","M-3004","M-3006","M-3008","M-3010","M-3012","M-3013"],
        "M-2002": ["M-3014","M-3015","M-3016"],
        "M-2003": ["M-3017","M-3018"],
        "M-2004": ["M-3011"],
        "M-2005": ["M-3009","M-3019","M-3020"],
    }
    for parent, children in semi_to_raw.items():
        for child in children:
            bom_data.append({
                "BOM_ID": f"BOM-{bom_id:04d}",
                "PARENT_MATERIAL_ID": parent,
                "CHILD_MATERIAL_ID": child,
                "QUANTITY_PER_UNIT": round(random.uniform(0.5,10), 2),
                "CREATED_AT": datetime.now()
            })
            bom_id += 1
    df_bom = pd.DataFrame(bom_data)

    # 4. Purchase Orders
    raw_mats = [m for m in materials_data if m["MATERIAL_GROUP"] == "RAW"]
    semi_mats = [m for m in materials_data if m["MATERIAL_GROUP"] == "SEMI"]
    mat_affinity = {
        "M-3001":["CHL","AUS","CHN"],"M-3002":["CHL","AUS","CHN"],"M-3003":["COD","CHN"],
        "M-3004":["CHN","JPN"],"M-3006":["CHN","JPN"],"M-3008":["CHL","USA"],
        "M-3009":["CHL","USA"],"M-3014":["USA","JPN","KOR","DEU"],
        "M-3015":["USA","JPN","KOR","DEU"],"M-3016":["DEU","JPN","USA"],
    }
    base_date = datetime(2025,1,1)
    po_data = []
    for i in range(120):
        mat = random.choice(raw_mats) if random.random() < 0.85 else random.choice(semi_mats)
        pref = mat_affinity.get(mat["MATERIAL_ID"], region_codes)
        pref_v = [v for v in vendors_data if v["COUNTRY_CODE"] in pref] or vendors_data
        v = random.choice(pref_v)
        qty = random.randint(500,10000) if mat["MATERIAL_GROUP"]=="RAW" else random.randint(50,500)
        price = mat["UNIT_COST"] * round(random.uniform(0.9, 1.15), 2)
        od = base_date + timedelta(days=random.randint(0,365))
        dd = od + timedelta(days=random.randint(14,90))
        po_data.append({
            "PO_ID": f"PO-{9001+i}",
            "VENDOR_ID": v["VENDOR_ID"],
            "MATERIAL_ID": mat["MATERIAL_ID"],
            "QUANTITY": qty,
            "UNIT_PRICE": round(price, 2),
            "ORDER_DATE": od.date(),
            "DELIVERY_DATE": dd.date(),
            "STATUS": random.choice(["OPEN","CLOSED","CLOSED","CLOSED"]),
            "CREATED_AT": datetime.now()
        })
    df_po = pd.DataFrame(po_data)

    # 5. Trade Data (with Outback Lithium Resources)
    tier2 = [
        {"name":"Outback Lithium Resources","country":"AUS","specialty":"lithium","concentration":0.25,"target_battery_mfg":True,"battery_coverage":0.85},
        {"name":"Cordillera Lithium Refining","country":"CHL","specialty":"lithium","concentration":0.15},
        {"name":"Altiplano Mining Corp","country":"CHL","specialty":"lithium","concentration":0.12},
        {"name":"Andean Copper Smelting","country":"CHL","specialty":"copper","concentration":0.25},
        {"name":"Katanga Cobalt Extraction","country":"COD","specialty":"cobalt","concentration":0.40},
        {"name":"Yangtze Graphite Processing","country":"CHN","specialty":"graphite","concentration":0.30},
        {"name":"Kansai Chemical Industries","country":"JPN","specialty":"electrolyte","concentration":0.35},
        {"name":"Rhineland Metals Refining","country":"DEU","specialty":"nickel","concentration":0.20},
        {"name":"Changjiang Cathode Materials","country":"CHN","specialty":"cathode","concentration":0.25},
        {"name":"Gyeongnam Precision Chemicals","country":"KOR","specialty":"separator","concentration":0.30},
    ]
    spec_hs = {
        "lithium":["2836.91","2825.20"],"copper":["7408.11","7409.11"],"cobalt":["8106.00"],
        "graphite":["3904.10"],"electrolyte":["2836.91"],"nickel":["7601.10"],
        "cathode":["8507.60"],"separator":["3904.10"],
    }
    batt_kw = ["battery","energy","power"]
    batt_mfg = [v for v in vendors_data if any(k in v["NAME"].lower() for k in batt_kw)]
    if not batt_mfg:
        batt_mfg = [v for v in vendors_data if v["COUNTRY_CODE"] in ["KOR","JPN","CHN"]][:10]
    qm_battery_targets = set()
    if batt_mfg:
        num_to_cover = max(1, int(len(batt_mfg) * 0.70))
        qm_target_list = random.sample(batt_mfg, num_to_cover)
        qm_battery_targets = {v["VENDOR_ID"] for v in qm_target_list}
        
    ports = {"CHL":"Port of Antofagasta","COD":"Port of Dar es Salaam","CHN":"Port of Shanghai",
             "JPN":"Port of Yokohama","KOR":"Port of Busan","DEU":"Port of Hamburg",
             "AUS":"Port of Fremantle","USA":"Port of Los Angeles","MEX":"Port of Manzanillo"}
    trade_data = []
    bol_id = 88001
    for i in range(150):
        t2 = random.choice(tier2)
        if t2["name"] == "Outback Lithium Resources":
            battery_coverage = t2.get("battery_coverage", 0.70)
            if batt_mfg and random.random() < battery_coverage:
                target_mfgs = [v for v in batt_mfg if v["VENDOR_ID"] in qm_battery_targets]
                consignee = random.choice(target_mfgs) if target_mfgs else random.choice(batt_mfg)
            else:
                consignee = random.choice(vendors_data)
        else:
            if random.random() < t2["concentration"]:
                if t2["specialty"] == "lithium" and batt_mfg:
                    consignee = random.choice(batt_mfg)
                else:
                    consignee = random.choice(vendors_data)
            else:
                consignee = random.choice(vendors_data)
                
        hs = random.choice(spec_hs.get(t2["specialty"], ["8507.60"]))
        sd = base_date + timedelta(days=random.randint(0,365))
        wt = random.randint(5000,50000)
        trade_data.append({
            "BOL_ID": f"BL-{bol_id}",
            "SHIPPER_NAME": t2["name"],
            "SHIPPER_COUNTRY": t2["country"],
            "CONSIGNEE_NAME": consignee["NAME"],
            "CONSIGNEE_COUNTRY": consignee["COUNTRY_CODE"],
            "HS_CODE": hs,
            "HS_DESCRIPTION": HS_CODES.get(hs, "Industrial Materials"),
            "SHIP_DATE": sd.date(),
            "WEIGHT_KG": float(wt),
            "VALUE_USD": round(wt * random.uniform(10,100), 2),
            "PORT_OF_ORIGIN": ports.get(t2["country"], "Unknown Port"),
            "PORT_OF_DESTINATION": ports.get(consignee["COUNTRY_CODE"], "Unknown Port"),
            "CREATED_AT": datetime.now()
        })
        bol_id += 1
    df_trade = pd.DataFrame(trade_data)

    # 6. PRODUCTS (New entity)
    products_data = [
        {"PRODUCT_ID": "P-100", "NAME": "Commercial EV Sedan 85kWh", "REVENUE_PER_UNIT": 55000.0, "CREATED_AT": datetime.now()},
        {"PRODUCT_ID": "P-200", "NAME": "Long-Range EV SUV 100kWh", "REVENUE_PER_UNIT": 72000.0, "CREATED_AT": datetime.now()},
        {"PRODUCT_ID": "P-300", "NAME": "Commercial EV Delivery Van", "REVENUE_PER_UNIT": 48000.0, "CREATED_AT": datetime.now()},
    ]
    df_products = pd.DataFrame(products_data)

    # 7. FACTORIES (New entity)
    factories_data = [
        {"FACTORY_ID": "F-01", "REGION_CODE": "USA", "CAPACITY": 1200.0, "PRODUCT_ID": "P-100", "CREATED_AT": datetime.now()},
        {"FACTORY_ID": "F-02", "REGION_CODE": "DEU", "CAPACITY": 950.0, "PRODUCT_ID": "P-200", "CREATED_AT": datetime.now()},
        {"FACTORY_ID": "F-03", "REGION_CODE": "MEX", "CAPACITY": 1500.0, "PRODUCT_ID": "P-300", "CREATED_AT": datetime.now()},
    ]
    df_factories = pd.DataFrame(factories_data)

    # 8. ORDERS (New entity)
    orders_data = []
    customers = ["Nordic Fleet Logistics", "Cascade Mobility", "Apex Delivery Solutions", "E-Trans Global", "Vanguard Motors"]
    for i in range(40):
        prod = random.choice(products_data)
        qty = random.randint(10, 80)
        rev = qty * prod["REVENUE_PER_UNIT"]
        due = datetime(2025, 6, 1) + timedelta(days=random.randint(10, 180))
        orders_data.append({
            "ORDER_ID": f"ORD-{7001+i}",
            "PRODUCT_ID": prod["PRODUCT_ID"],
            "CUSTOMER_ID": random.choice(customers),
            "QUANTITY": qty,
            "REVENUE": rev,
            "DUE_DATE": due.date(),
            "STATUS": random.choice(["OPEN", "PROCESSING", "OPEN", "SCHEDULED"]),
            "CREATED_AT": datetime.now()
        })
    df_orders = pd.DataFrame(orders_data)

    # 9. INVENTORY (New entity)
    inventory_data = []
    for f in factories_data:
        for m in raw_mats[:15]:
            on_hand = float(random.randint(200, 3000))
            safety = float(random.randint(300, 1200))
            reorder = safety + (m["UNIT_COST"] * 5)
            inventory_data.append({
                "MATERIAL_ID": m["MATERIAL_ID"],
                "FACTORY_ID": f["FACTORY_ID"],
                "ON_HAND_QTY": on_hand,
                "SAFETY_STOCK": safety,
                "REORDER_POINT": reorder,
                "UPDATED_AT": datetime.now()
            })
    df_inventory = pd.DataFrame(inventory_data)

    # 10. SHIPMENTS (New entity)
    shipments_data = []
    for i, po in enumerate(po_data[:30]):
        eta = datetime.now() + timedelta(days=random.randint(3, 25))
        shipments_data.append({
            "SHIPMENT_ID": f"SHP-{3001+i}",
            "PO_ID": po["PO_ID"],
            "ORIGIN": ports.get(random.choice(region_codes), "Port of Shanghai"),
            "DESTINATION": "Port of Long Beach",
            "STATUS": random.choice(["IN_TRANSIT", "CUSTOMS_HOLD", "IN_TRANSIT", "DELIVERED"]),
            "ETA": eta.date(),
            "CREATED_AT": datetime.now()
        })
    df_shipments = pd.DataFrame(shipments_data)

    # 11. ALERTS (New entity)
    alerts_data = [
        {"ALERT_ID": "ALT-101", "SEVERITY": "CRITICAL", "TRIGGER_TYPE": "HIDDEN_DEPENDENCY", "ENTITY_TYPE": "VENDOR", "ENTITY_ID": "V10001", "MESSAGE": "Undisclosed upstream bottleneck detected: Outback Lithium Resources supplies 70%+ of cathode tier.", "IS_PREDICTIVE": False, "STATUS": "ACTIVE", "CREATED_AT": datetime.now()},
        {"ALERT_ID": "ALT-102", "SEVERITY": "HIGH", "TRIGGER_TYPE": "GEOPOLITICAL_RISK", "ENTITY_TYPE": "REGION", "ENTITY_ID": "COD", "MESSAGE": "Heightened export scrutiny on cobalt transit routes through Central Africa corridors.", "IS_PREDICTIVE": False, "STATUS": "ACTIVE", "CREATED_AT": datetime.now() - timedelta(hours=3)},
        {"ALERT_ID": "ALT-103", "SEVERITY": "WARNING", "TRIGGER_TYPE": "STOCKOUT_PREDICTION", "ENTITY_TYPE": "MATERIAL", "ENTITY_ID": "M-3012", "MESSAGE": "Projected stockout within 18 days at Factory F-01 due to supplier delivery delays.", "IS_PREDICTIVE": True, "STATUS": "ACTIVE", "CREATED_AT": datetime.now() - timedelta(hours=5)},
    ]
    df_alerts = pd.DataFrame(alerts_data)

    # 12. SCENARIOS (New entity)
    scenarios_data = [
        {"SCENARIO_ID": "SCEN-01", "NAME": "Australian Lithium Port Embargo", "SCENARIO_TYPE": "REGIONAL_DISRUPTION", "TARGET_ENTITY_TYPE": "REGION", "TARGET_ENTITY_ID": "AUS", "INTENSITY": 0.85, "DURATION_DAYS": 45, "PARAMETERS_JSON": '{"port_closure": true}', "CREATED_AT": datetime.now()},
        {"SCENARIO_ID": "SCEN-02", "NAME": "Primary Cobalt Refiner Solvency Event", "SCENARIO_TYPE": "VENDOR_FAILURE", "TARGET_ENTITY_TYPE": "VENDOR", "TARGET_ENTITY_ID": "V10003", "INTENSITY": 1.0, "DURATION_DAYS": 60, "PARAMETERS_JSON": '{"capacity_loss": 1.0}', "CREATED_AT": datetime.now()},
    ]
    df_scenarios = pd.DataFrame(scenarios_data)

    # 13. MODEL_VERSIONS (Synthetic seed placeholder rows, clearly labeled per P0-3)
    models_data = [
        {"MODEL_NAME": "RiskScoreRegressor", "VERSION": "v1.0.0-synthetic", "TRAINING_DATE": datetime.now() - timedelta(days=7), "DATASET_VERSION": "seed_42_synthetic", "METRICS_JSON": '{"PR_AUC": 0.88, "F1": 0.82, "Accuracy": 0.89}', "STATUS": "SYNTHETIC_DEMO", "NOTE": "illustrative placeholder — no model has been trained"},
        {"MODEL_NAME": "StockoutClassifier", "VERSION": "v1.0.0-synthetic", "TRAINING_DATE": datetime.now() - timedelta(days=14), "DATASET_VERSION": "seed_42_synthetic", "METRICS_JSON": '{"PR_AUC": 0.84, "F1": 0.79}', "STATUS": "SYNTHETIC_DEMO", "NOTE": "illustrative placeholder — no model has been trained"},
        {"MODEL_NAME": "JaccardLinkPredictor", "VERSION": "v1.0.0-synthetic", "TRAINING_DATE": datetime.now() - timedelta(days=3), "DATASET_VERSION": "seed_42_synthetic", "METRICS_JSON": '{"precision_at_10": 0.90}', "STATUS": "SYNTHETIC_DEMO", "NOTE": "illustrative placeholder — no model has been trained"},
    ]
    df_models = pd.DataFrame(models_data)

    return {
        "VENDORS": df_vendors,
        "MATERIALS": df_materials,
        "PURCHASE_ORDERS": df_po,
        "BILL_OF_MATERIALS": df_bom,
        "TRADE_DATA": df_trade,
        "REGIONS": df_regions,
        "PRODUCTS": df_products,
        "FACTORIES": df_factories,
        "ORDERS": df_orders,
        "INVENTORY": df_inventory,
        "SHIPMENTS": df_shipments,
        "ALERTS": df_alerts,
        "SCENARIOS": df_scenarios,
        "MODEL_VERSIONS": df_models,
    }

def seed_database(repo: BaseRepository, seed: int = 42, overwrite: bool = False) -> bool:
    """Generate synthetic dataset and write to repository."""
    logger.info(f"Generating synthetic dataset with seed {seed}...")
    tables = generate_all_data(seed=seed)
    success = True
    for table_name, df in tables.items():
        written = repo.write_table(df, table_name, overwrite=overwrite)
        if not written:
            logger.warning(f"Failed to write table {table_name}")
            success = False
    logger.info("Synthetic database seeding completed.")
    return success
