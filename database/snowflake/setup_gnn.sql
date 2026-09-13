/******************************************************************************
 * GNN SUPPLY CHAIN RISK ANALYSIS - GNN-ONLY SETUP SCRIPT
 * 
 * Purpose: Deploy a Graph Neural Network-powered supply chain risk analysis
 *          platform on Snowflake using PyTorch Geometric, Cortex Agent, and
 *          a multi-page Streamlit dashboard.
 * Domain: Manufacturing / Supply Chain
 * 
 * What This Script Does:
 * 1.  Creates role, warehouse, database, and schema
 * 2.  Creates compute pool for GPU notebooks
 * 3.  Creates network rules and external access integration for PyPI
 * 4.  Creates Git integration and repository
 * 5.  Creates stages for notebooks and semantic models
 * 6.  Creates tables (input ERP data + GNN output tables)
 * 7.  Creates views for analytics
 * 8.  Generates synthetic ERP data via stored procedure
 * 9.  Creates risk analysis UDF
 * 10. Deploys GPU notebook (PyTorch Geometric GNN training)
 * 11. Uploads semantic model for Cortex Analyst
 * 12. Deploys GNN Streamlit dashboard
 * 13. Creates GNN compatibility views
 * 14. Creates Cortex Agent
 * 
 * Prerequisites:
 *   - Snowflake account with ACCOUNTADMIN role
 *   - Cortex AI features enabled
 *   - GPU compute pool support (GPU_NV_S instance family)
 *   - External Access Integration support (not available on trial accounts)
 ******************************************************************************/

USE ROLE ACCOUNTADMIN;

ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"supply_chain_risk_intelligence_with_snowflake","version":{"major":1,"minor":0},"attributes":{"is_quickstart":1,"source":"sql"}}';

SET USERNAME = (SELECT CURRENT_USER());

--------------------------------------------------------------------------------
-- STEP 1: CREATE ROLE
--------------------------------------------------------------------------------

CREATE OR REPLACE ROLE SUPPLY_CHAIN_RISK_ROLE;
GRANT ROLE SUPPLY_CHAIN_RISK_ROLE TO USER IDENTIFIER($USERNAME);
GRANT ROLE SUPPLY_CHAIN_RISK_ROLE TO ROLE SYSADMIN;

GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE SUPPLY_CHAIN_RISK_ROLE;

--------------------------------------------------------------------------------
-- STEP 2: CREATE WAREHOUSE (as ACCOUNTADMIN, grant to demo role)
--------------------------------------------------------------------------------

CREATE OR REPLACE WAREHOUSE SUPPLY_CHAIN_RISK_WH
    WAREHOUSE_SIZE = SMALL
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for GNN Supply Chain Risk SQL operations';

GRANT USAGE ON WAREHOUSE SUPPLY_CHAIN_RISK_WH TO ROLE SUPPLY_CHAIN_RISK_ROLE;
GRANT OPERATE ON WAREHOUSE SUPPLY_CHAIN_RISK_WH TO ROLE SUPPLY_CHAIN_RISK_ROLE;

USE WAREHOUSE SUPPLY_CHAIN_RISK_WH;

--------------------------------------------------------------------------------
-- STEP 3: CREATE DATABASE AND SCHEMA (as ACCOUNTADMIN, grant to demo role)
--------------------------------------------------------------------------------

CREATE OR REPLACE DATABASE SUPPLY_CHAIN_RISK
    COMMENT = 'GNN-powered supply chain risk analysis platform';

CREATE SCHEMA IF NOT EXISTS SUPPLY_CHAIN_RISK.SUPPLY_CHAIN_RISK
    COMMENT = 'Supply chain data, GNN outputs, and application objects';

GRANT OWNERSHIP ON DATABASE SUPPLY_CHAIN_RISK TO ROLE SUPPLY_CHAIN_RISK_ROLE COPY CURRENT GRANTS;
GRANT OWNERSHIP ON SCHEMA SUPPLY_CHAIN_RISK.SUPPLY_CHAIN_RISK TO ROLE SUPPLY_CHAIN_RISK_ROLE COPY CURRENT GRANTS;

--------------------------------------------------------------------------------
-- STEP 4: SNOWFLAKE INTELLIGENCE AND CORTEX SETUP
--------------------------------------------------------------------------------

ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

CREATE SNOWFLAKE INTELLIGENCE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;

GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE SUPPLY_CHAIN_RISK_ROLE;
GRANT MODIFY ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE SUPPLY_CHAIN_RISK_ROLE;

GRANT CREATE AGENT ON SCHEMA SUPPLY_CHAIN_RISK.SUPPLY_CHAIN_RISK TO ROLE SUPPLY_CHAIN_RISK_ROLE;
-- Account-level grant required for Cortex Agents to serve endpoints (no scoped alternative available)
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE SUPPLY_CHAIN_RISK_ROLE;

--------------------------------------------------------------------------------
-- STEP 5: CREATE COMPUTE POOL (as ACCOUNTADMIN, grant to demo role)
--------------------------------------------------------------------------------

CREATE COMPUTE POOL IF NOT EXISTS SUPPLY_CHAIN_RISK_COMPUTE_POOL
    MIN_NODES = 1
    MAX_NODES = 1
    INSTANCE_FAMILY = GPU_NV_S
    AUTO_RESUME = TRUE
    AUTO_SUSPEND_SECS = 600
    COMMENT = 'GPU compute pool for PyTorch Geometric GNN training';

GRANT USAGE ON COMPUTE POOL SUPPLY_CHAIN_RISK_COMPUTE_POOL TO ROLE SUPPLY_CHAIN_RISK_ROLE;
GRANT MONITOR ON COMPUTE POOL SUPPLY_CHAIN_RISK_COMPUTE_POOL TO ROLE SUPPLY_CHAIN_RISK_ROLE;
GRANT OPERATE ON COMPUTE POOL SUPPLY_CHAIN_RISK_COMPUTE_POOL TO ROLE SUPPLY_CHAIN_RISK_ROLE;

--------------------------------------------------------------------------------
-- STEP 6: CREATE NETWORK RULES AND EXTERNAL ACCESS INTEGRATION
--------------------------------------------------------------------------------

CREATE OR REPLACE NETWORK RULE SUPPLY_CHAIN_RISK.SUPPLY_CHAIN_RISK.SUPPLY_CHAIN_RISK_EGRESS_RULE
    TYPE = HOST_PORT
    MODE = EGRESS
    VALUE_LIST = (
        'pypi.org:443',
        'files.pythonhosted.org:443',
        'download.pytorch.org:443',
        'data.pyg.org:443'
    )
    COMMENT = 'Required for PyTorch Geometric and dependencies';

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION SUPPLY_CHAIN_RISK_EXTERNAL_ACCESS
    ALLOWED_NETWORK_RULES = (SUPPLY_CHAIN_RISK.SUPPLY_CHAIN_RISK.SUPPLY_CHAIN_RISK_EGRESS_RULE)
    ENABLED = TRUE;

GRANT USAGE ON INTEGRATION SUPPLY_CHAIN_RISK_EXTERNAL_ACCESS TO ROLE SUPPLY_CHAIN_RISK_ROLE;

--------------------------------------------------------------------------------
-- STEP 7: GIT REPOSITORY INTEGRATION (PUBLIC REPO)
--------------------------------------------------------------------------------

CREATE OR REPLACE API INTEGRATION SUPPLY_CHAIN_RISK_GIT_API_INTEGRATION
    API_PROVIDER = git_https_api
    API_ALLOWED_PREFIXES = ('https://github.com/Snowflake-Labs/')
    ENABLED = TRUE;

GRANT USAGE ON INTEGRATION SUPPLY_CHAIN_RISK_GIT_API_INTEGRATION TO ROLE SUPPLY_CHAIN_RISK_ROLE;

USE ROLE SUPPLY_CHAIN_RISK_ROLE;
USE DATABASE SUPPLY_CHAIN_RISK;
USE SCHEMA SUPPLY_CHAIN_RISK;

CREATE OR REPLACE GIT REPOSITORY SUPPLY_CHAIN_RISK.SUPPLY_CHAIN_RISK.SUPPLY_CHAIN_RISK_REPO
    API_INTEGRATION = SUPPLY_CHAIN_RISK_GIT_API_INTEGRATION
    ORIGIN = 'https://github.com/Snowflake-Labs/sfguide-supply-chain-risk-intelligence-with-snowflake';

--------------------------------------------------------------------------------
-- STEP 8: CREATE STAGES
--------------------------------------------------------------------------------

CREATE STAGE IF NOT EXISTS MODELS_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for ML models and notebooks';

CREATE STAGE IF NOT EXISTS SEMANTIC_MODELS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for semantic model YAML files';

--------------------------------------------------------------------------------
-- STEP 9: CREATE TABLES - ERP DATA (Input)
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS VENDORS (
    VENDOR_ID VARCHAR(20) PRIMARY KEY,
    NAME VARCHAR(255) NOT NULL,
    COUNTRY_CODE VARCHAR(3) NOT NULL,
    CITY VARCHAR(100),
    PHONE VARCHAR(50),
    TIER NUMBER DEFAULT 1,
    FINANCIAL_HEALTH_SCORE FLOAT DEFAULT 0.5,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Vendor master data - known Tier 1 suppliers from ERP';

CREATE TABLE IF NOT EXISTS MATERIALS (
    MATERIAL_ID VARCHAR(20) PRIMARY KEY,
    DESCRIPTION VARCHAR(255) NOT NULL,
    MATERIAL_GROUP VARCHAR(10) NOT NULL,
    UNIT_OF_MEASURE VARCHAR(10) DEFAULT 'PC',
    CRITICALITY_SCORE FLOAT DEFAULT 0.5,
    INVENTORY_DAYS NUMBER DEFAULT 30,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Material master - parts and products hierarchy';

CREATE TABLE IF NOT EXISTS PURCHASE_ORDERS (
    PO_ID VARCHAR(20) PRIMARY KEY,
    VENDOR_ID VARCHAR(20) NOT NULL,
    MATERIAL_ID VARCHAR(20) NOT NULL,
    QUANTITY NUMBER NOT NULL,
    UNIT_PRICE FLOAT NOT NULL,
    ORDER_DATE DATE NOT NULL,
    DELIVERY_DATE DATE,
    STATUS VARCHAR(20) DEFAULT 'OPEN',
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    FOREIGN KEY (VENDOR_ID) REFERENCES VENDORS(VENDOR_ID),
    FOREIGN KEY (MATERIAL_ID) REFERENCES MATERIALS(MATERIAL_ID)
)
COMMENT = 'Purchase orders - known supplier to part edges';

CREATE TABLE IF NOT EXISTS BILL_OF_MATERIALS (
    BOM_ID VARCHAR(20) PRIMARY KEY,
    PARENT_MATERIAL_ID VARCHAR(20) NOT NULL,
    CHILD_MATERIAL_ID VARCHAR(20) NOT NULL,
    QUANTITY_PER_UNIT FLOAT NOT NULL DEFAULT 1.0,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    FOREIGN KEY (PARENT_MATERIAL_ID) REFERENCES MATERIALS(MATERIAL_ID),
    FOREIGN KEY (CHILD_MATERIAL_ID) REFERENCES MATERIALS(MATERIAL_ID)
)
COMMENT = 'Bill of materials - part assembly hierarchy';

CREATE TABLE IF NOT EXISTS TRADE_DATA (
    BOL_ID VARCHAR(20) PRIMARY KEY,
    SHIPPER_NAME VARCHAR(255) NOT NULL,
    SHIPPER_COUNTRY VARCHAR(3),
    CONSIGNEE_NAME VARCHAR(255) NOT NULL,
    CONSIGNEE_COUNTRY VARCHAR(3),
    HS_CODE VARCHAR(10) NOT NULL,
    HS_DESCRIPTION VARCHAR(255),
    SHIP_DATE DATE NOT NULL,
    WEIGHT_KG FLOAT,
    VALUE_USD FLOAT,
    PORT_OF_ORIGIN VARCHAR(100),
    PORT_OF_DESTINATION VARCHAR(100),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'External trade data - bills of lading for Tier 2+ inference';

CREATE TABLE IF NOT EXISTS REGIONS (
    REGION_CODE VARCHAR(3) PRIMARY KEY,
    REGION_NAME VARCHAR(100) NOT NULL,
    BASE_RISK_SCORE FLOAT DEFAULT 0.0,
    GEOPOLITICAL_RISK FLOAT DEFAULT 0.0,
    NATURAL_DISASTER_RISK FLOAT DEFAULT 0.0,
    INFRASTRUCTURE_SCORE FLOAT DEFAULT 0.5,
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Geographic region risk factors';

--------------------------------------------------------------------------------
-- STEP 10: CREATE TABLES - GNN MODEL OUTPUTS
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS RISK_SCORES (
    SCORE_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    NODE_ID VARCHAR(50) NOT NULL,
    NODE_TYPE VARCHAR(20) NOT NULL,
    RISK_SCORE FLOAT NOT NULL,
    RISK_CATEGORY VARCHAR(20),
    CONFIDENCE FLOAT,
    EMBEDDING ARRAY,
    CONTRIBUTING_FACTORS VARIANT,
    MODEL_VERSION VARCHAR(50),
    CALCULATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'GNN-computed risk scores for all supply chain nodes';

CREATE TABLE IF NOT EXISTS PREDICTED_LINKS (
    LINK_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    SOURCE_NODE_ID VARCHAR(50) NOT NULL,
    SOURCE_NODE_TYPE VARCHAR(20) NOT NULL,
    TARGET_NODE_ID VARCHAR(50) NOT NULL,
    TARGET_NODE_TYPE VARCHAR(20) NOT NULL,
    LINK_TYPE VARCHAR(50) NOT NULL,
    PROBABILITY FLOAT NOT NULL,
    EVIDENCE_STRENGTH VARCHAR(20),
    SUPPORTING_DATA VARIANT,
    MODEL_VERSION VARCHAR(50),
    PREDICTED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'GNN-predicted unknown supplier relationships';

CREATE TABLE IF NOT EXISTS BOTTLENECKS (
    BOTTLENECK_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    NODE_ID VARCHAR(50) NOT NULL,
    NODE_TYPE VARCHAR(20) NOT NULL,
    DEPENDENT_COUNT NUMBER NOT NULL,
    DEPENDENT_NODES ARRAY,
    IMPACT_SCORE FLOAT NOT NULL,
    DESCRIPTION VARCHAR(500),
    MITIGATION_STATUS VARCHAR(20) DEFAULT 'UNMITIGATED',
    MODEL_VERSION VARCHAR(50),
    IDENTIFIED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Identified single points of failure in supply chain';

--------------------------------------------------------------------------------
-- STEP 11: CREATE VIEWS FOR ANALYTICS
--------------------------------------------------------------------------------

CREATE OR REPLACE VIEW VW_SUPPLIER_RISK AS
SELECT 
    v.VENDOR_ID,
    v.NAME AS VENDOR_NAME,
    v.COUNTRY_CODE,
    v.TIER,
    r.BASE_RISK_SCORE AS REGION_RISK,
    rs.RISK_SCORE AS GNN_RISK_SCORE,
    rs.RISK_CATEGORY,
    rs.CONFIDENCE,
    COALESCE(po_stats.TOTAL_ORDERS, 0) AS TOTAL_ORDERS,
    COALESCE(po_stats.TOTAL_VALUE, 0) AS TOTAL_ORDER_VALUE
FROM VENDORS v
LEFT JOIN REGIONS r ON v.COUNTRY_CODE = r.REGION_CODE
LEFT JOIN RISK_SCORES rs ON v.VENDOR_ID = rs.NODE_ID AND rs.NODE_TYPE = 'SUPPLIER'
LEFT JOIN (
    SELECT VENDOR_ID, COUNT(*) AS TOTAL_ORDERS, SUM(QUANTITY * UNIT_PRICE) AS TOTAL_VALUE
    FROM PURCHASE_ORDERS
    GROUP BY VENDOR_ID
) po_stats ON v.VENDOR_ID = po_stats.VENDOR_ID;

CREATE OR REPLACE VIEW VW_MATERIAL_RISK AS
SELECT 
    m.MATERIAL_ID,
    m.DESCRIPTION,
    m.MATERIAL_GROUP,
    m.CRITICALITY_SCORE,
    rs.RISK_SCORE AS GNN_RISK_SCORE,
    rs.RISK_CATEGORY,
    COALESCE(supplier_count.NUM_SUPPLIERS, 0) AS NUM_SUPPLIERS,
    COALESCE(supplier_count.AVG_SUPPLIER_RISK, 0) AS AVG_SUPPLIER_RISK
FROM MATERIALS m
LEFT JOIN RISK_SCORES rs ON m.MATERIAL_ID = rs.NODE_ID AND rs.NODE_TYPE = 'PART'
LEFT JOIN (
    SELECT 
        po.MATERIAL_ID,
        COUNT(DISTINCT po.VENDOR_ID) AS NUM_SUPPLIERS,
        AVG(COALESCE(rs2.RISK_SCORE, 0.5)) AS AVG_SUPPLIER_RISK
    FROM PURCHASE_ORDERS po
    LEFT JOIN RISK_SCORES rs2 ON po.VENDOR_ID = rs2.NODE_ID AND rs2.NODE_TYPE = 'SUPPLIER'
    GROUP BY po.MATERIAL_ID
) supplier_count ON m.MATERIAL_ID = supplier_count.MATERIAL_ID;

CREATE OR REPLACE VIEW VW_UNKNOWN_DEPENDENCIES AS
SELECT 
    pl.LINK_ID,
    pl.SOURCE_NODE_ID,
    pl.SOURCE_NODE_TYPE,
    CASE 
        WHEN pl.SOURCE_NODE_TYPE = 'SUPPLIER' THEN v1.NAME
        ELSE pl.SOURCE_NODE_ID
    END AS SOURCE_NAME,
    pl.TARGET_NODE_ID,
    pl.TARGET_NODE_TYPE,
    CASE 
        WHEN pl.TARGET_NODE_TYPE = 'SUPPLIER' THEN v2.NAME
        ELSE pl.TARGET_NODE_ID
    END AS TARGET_NAME,
    pl.PROBABILITY,
    pl.EVIDENCE_STRENGTH,
    pl.PREDICTED_AT
FROM PREDICTED_LINKS pl
LEFT JOIN VENDORS v1 ON pl.SOURCE_NODE_ID = v1.VENDOR_ID
LEFT JOIN VENDORS v2 ON pl.TARGET_NODE_ID = v2.VENDOR_ID
WHERE pl.PROBABILITY >= 0.5
ORDER BY pl.PROBABILITY DESC;

CREATE OR REPLACE VIEW VW_RISK_SUMMARY AS
SELECT 
    'SUPPLIERS' AS CATEGORY,
    COUNT(*) AS TOTAL_COUNT,
    SUM(CASE WHEN RISK_CATEGORY = 'CRITICAL' THEN 1 ELSE 0 END) AS CRITICAL_COUNT,
    SUM(CASE WHEN RISK_CATEGORY = 'HIGH' THEN 1 ELSE 0 END) AS HIGH_COUNT,
    SUM(CASE WHEN RISK_CATEGORY = 'MEDIUM' THEN 1 ELSE 0 END) AS MEDIUM_COUNT,
    SUM(CASE WHEN RISK_CATEGORY = 'LOW' THEN 1 ELSE 0 END) AS LOW_COUNT,
    AVG(RISK_SCORE) AS AVG_RISK_SCORE
FROM RISK_SCORES WHERE NODE_TYPE = 'SUPPLIER'
UNION ALL
SELECT 
    'PARTS' AS CATEGORY,
    COUNT(*) AS TOTAL_COUNT,
    SUM(CASE WHEN RISK_CATEGORY = 'CRITICAL' THEN 1 ELSE 0 END) AS CRITICAL_COUNT,
    SUM(CASE WHEN RISK_CATEGORY = 'HIGH' THEN 1 ELSE 0 END) AS HIGH_COUNT,
    SUM(CASE WHEN RISK_CATEGORY = 'MEDIUM' THEN 1 ELSE 0 END) AS MEDIUM_COUNT,
    SUM(CASE WHEN RISK_CATEGORY = 'LOW' THEN 1 ELSE 0 END) AS LOW_COUNT,
    AVG(RISK_SCORE) AS AVG_RISK_SCORE
FROM RISK_SCORES WHERE NODE_TYPE = 'PART';

--------------------------------------------------------------------------------
-- STEP 12: GENERATE AND LOAD SYNTHETIC DATA
-- Creates a Snowpark Python stored procedure that generates realistic EV battery
-- supply chain data directly into tables.
-- The "Outback Lithium Resources" unknown bottleneck pattern is embedded in trade data.
--------------------------------------------------------------------------------

CREATE OR REPLACE PROCEDURE GENERATE_SYNTHETIC_DATA(SEED INT DEFAULT 42)
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'pandas')
HANDLER = 'run'
AS
$$
def run(session, seed=42):
    import random
    import pandas as pd
    from datetime import datetime, timedelta

    random.seed(seed)

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

    # ── REGIONS ──
    regions_data = []
    for code, risks in REGION_RISKS.items():
        regions_data.append({
            "REGION_CODE": code, "REGION_NAME": REGIONS_CFG[code]["name"],
            "BASE_RISK_SCORE": risks["base"], "GEOPOLITICAL_RISK": risks["geopolitical"],
            "NATURAL_DISASTER_RISK": risks["natural"], "INFRASTRUCTURE_SCORE": risks["infrastructure"],
        })

    # ── VENDORS ──
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
            "VENDOR_ID": f"V{10001+i}", "NAME": name, "COUNTRY_CODE": region,
            "CITY": city, "PHONE": phone, "TIER": 1,
            "FINANCIAL_HEALTH_SCORE": round(random.uniform(0.3, 0.95), 2),
        })

    # ── MATERIALS + BOM ──
    finished = [{"id":"M-1000","desc":"EV Battery Pack 85kWh","group":"FIN","unit":"PC","crit":1.0}]
    semi = [
        {"id":"M-2001","desc":"Battery Module 400V","group":"SEMI","unit":"PC","crit":0.95},
        {"id":"M-2002","desc":"Battery Management System","group":"SEMI","unit":"PC","crit":0.9},
        {"id":"M-2003","desc":"Thermal Management Assembly","group":"SEMI","unit":"PC","crit":0.85},
        {"id":"M-2004","desc":"Battery Enclosure Assembly","group":"SEMI","unit":"PC","crit":0.8},
        {"id":"M-2005","desc":"High-Voltage Harness","group":"SEMI","unit":"PC","crit":0.85},
    ]
    raw = [
        {"id":"M-3001","desc":"Lithium Hydroxide Grade A","group":"RAW","unit":"KG","crit":0.95},
        {"id":"M-3002","desc":"Lithium Carbonate Battery Grade","group":"RAW","unit":"KG","crit":0.95},
        {"id":"M-3003","desc":"Cobalt Oxide Powder","group":"RAW","unit":"KG","crit":0.9},
        {"id":"M-3004","desc":"Nickel Sulfate Battery Grade","group":"RAW","unit":"KG","crit":0.85},
        {"id":"M-3005","desc":"Manganese Dioxide","group":"RAW","unit":"KG","crit":0.75},
        {"id":"M-3006","desc":"Synthetic Graphite Anode","group":"RAW","unit":"KG","crit":0.85},
        {"id":"M-3007","desc":"Silicon Anode Additive","group":"RAW","unit":"KG","crit":0.7},
        {"id":"M-3008","desc":"Copper Foil 8 Micron","group":"RAW","unit":"KG","crit":0.85},
        {"id":"M-3009","desc":"Copper Busbar 5mm","group":"RAW","unit":"KG","crit":0.8},
        {"id":"M-3010","desc":"Aluminum Foil 15 Micron","group":"RAW","unit":"KG","crit":0.8},
        {"id":"M-3011","desc":"Aluminum Housing Profile","group":"RAW","unit":"KG","crit":0.7},
        {"id":"M-3012","desc":"Electrolyte LiPF6 Solution","group":"RAW","unit":"L","crit":0.9},
        {"id":"M-3013","desc":"Ceramic Coated Separator","group":"RAW","unit":"M2","crit":0.9},
        {"id":"M-3014","desc":"BMS Controller IC","group":"RAW","unit":"PC","crit":0.85},
        {"id":"M-3015","desc":"Cell Monitoring ASIC","group":"RAW","unit":"PC","crit":0.85},
        {"id":"M-3016","desc":"Power MOSFET Module","group":"RAW","unit":"PC","crit":0.8},
        {"id":"M-3017","desc":"Thermal Interface Material","group":"RAW","unit":"KG","crit":0.75},
        {"id":"M-3018","desc":"Cooling Plate Aluminum","group":"RAW","unit":"PC","crit":0.7},
        {"id":"M-3019","desc":"High-Voltage Cable 35mm2","group":"RAW","unit":"M","crit":0.8},
        {"id":"M-3020","desc":"Connector Assembly HV","group":"RAW","unit":"PC","crit":0.75},
    ]
    materials_data = []
    for m in finished + semi + raw:
        materials_data.append({
            "MATERIAL_ID": m["id"], "DESCRIPTION": m["desc"], "MATERIAL_GROUP": m["group"],
            "UNIT_OF_MEASURE": m["unit"], "CRITICALITY_SCORE": m["crit"],
            "INVENTORY_DAYS": random.randint(15, 60),
        })
    bom_data = []
    bom_id = 1
    for s in semi:
        bom_data.append({"BOM_ID": f"BOM-{bom_id:04d}", "PARENT_MATERIAL_ID": "M-1000",
                          "CHILD_MATERIAL_ID": s["id"], "QUANTITY_PER_UNIT": random.randint(1,4)})
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
            bom_data.append({"BOM_ID": f"BOM-{bom_id:04d}", "PARENT_MATERIAL_ID": parent,
                              "CHILD_MATERIAL_ID": child, "QUANTITY_PER_UNIT": round(random.uniform(0.5,10),2)})
            bom_id += 1

    # ── PURCHASE ORDERS ──
    raw_mats = [m for m in materials_data if m["MATERIAL_GROUP"] == "RAW"]
    semi_mats = [m for m in materials_data if m["MATERIAL_GROUP"] == "SEMI"]
    mat_affinity = {
        "M-3001":["CHL","AUS","CHN"],"M-3002":["CHL","AUS","CHN"],"M-3003":["COD","CHN"],
        "M-3004":["CHN","JPN"],"M-3006":["CHN","JPN"],"M-3008":["CHL","USA"],
        "M-3009":["CHL","USA"],"M-3014":["USA","JPN","KOR","DEU"],
        "M-3015":["USA","JPN","KOR","DEU"],"M-3016":["DEU","JPN","USA"],
    }
    base_date = datetime(2023,1,1)
    po_data = []
    for i in range(120):
        mat = random.choice(raw_mats) if random.random() < 0.85 else random.choice(semi_mats)
        pref = mat_affinity.get(mat["MATERIAL_ID"], region_codes)
        pref_v = [v for v in vendors_data if v["COUNTRY_CODE"] in pref] or vendors_data
        v = random.choice(pref_v)
        qty = random.randint(500,10000) if mat["MATERIAL_GROUP"]=="RAW" else random.randint(50,500)
        price = round(random.uniform(5,500),2) if mat["MATERIAL_GROUP"]=="RAW" else round(random.uniform(500,5000),2)
        od = base_date + timedelta(days=random.randint(0,365))
        dd = od + timedelta(days=random.randint(14,90))
        po_data.append({
            "PO_ID": f"PO-{9001+i}", "VENDOR_ID": v["VENDOR_ID"], "MATERIAL_ID": mat["MATERIAL_ID"],
            "QUANTITY": qty, "UNIT_PRICE": price, "ORDER_DATE": od.strftime("%Y-%m-%d"),
            "DELIVERY_DATE": dd.strftime("%Y-%m-%d"), "STATUS": random.choice(["OPEN","CLOSED","CLOSED","CLOSED"]),
        })

    # ── TRADE DATA (with Outback Lithium Resources unknown bottleneck) ──
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
        "graphite":["3801.10"],"electrolyte":["2826.19"],"nickel":["7502.10"],
        "cathode":["8507.90"],"separator":["3920.10"],
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
                if target_mfgs:
                    consignee = random.choice(target_mfgs)
                else:
                    consignee = random.choice(batt_mfg)
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
            "BOL_ID": f"BL-{bol_id}", "SHIPPER_NAME": t2["name"], "SHIPPER_COUNTRY": t2["country"],
            "CONSIGNEE_NAME": consignee["NAME"], "CONSIGNEE_COUNTRY": consignee["COUNTRY_CODE"],
            "HS_CODE": hs, "HS_DESCRIPTION": HS_CODES.get(hs, "Industrial Materials"),
            "SHIP_DATE": sd.strftime("%Y-%m-%d"), "WEIGHT_KG": wt,
            "VALUE_USD": round(wt * random.uniform(10,100), 2),
            "PORT_OF_ORIGIN": ports.get(t2["country"], "Unknown Port"),
            "PORT_OF_DESTINATION": ports.get(consignee["COUNTRY_CODE"], "Unknown Port"),
        })
        bol_id += 1

    covered = {r["CONSIGNEE_NAME"] for r in trade_data}
    for v in vendors_data:
        if v["NAME"] not in covered:
            t2 = random.choice(tier2)
            hs = random.choice(spec_hs.get(t2["specialty"], ["8507.60"]))
            sd = base_date + timedelta(days=random.randint(0,365))
            wt = random.randint(5000,50000)
            trade_data.append({
                "BOL_ID": f"BL-{bol_id}", "SHIPPER_NAME": t2["name"], "SHIPPER_COUNTRY": t2["country"],
                "CONSIGNEE_NAME": v["NAME"], "CONSIGNEE_COUNTRY": v["COUNTRY_CODE"],
                "HS_CODE": hs, "HS_DESCRIPTION": HS_CODES.get(hs, "Industrial Materials"),
                "SHIP_DATE": sd.strftime("%Y-%m-%d"), "WEIGHT_KG": wt,
                "VALUE_USD": round(wt * random.uniform(10,100), 2),
                "PORT_OF_ORIGIN": ports.get(t2["country"], "Unknown Port"),
                "PORT_OF_DESTINATION": ports.get(v["COUNTRY_CODE"], "Unknown Port"),
            })
            bol_id += 1

    # ── LOAD INTO TABLES ──
    tables = ["TRADE_DATA","PURCHASE_ORDERS","BILL_OF_MATERIALS","MATERIALS","VENDORS","REGIONS"]
    for t in tables:
        session.sql(f"TRUNCATE TABLE IF EXISTS {t}").collect()

    datasets = [
        ("REGIONS", regions_data), ("VENDORS", vendors_data), ("MATERIALS", materials_data),
        ("BILL_OF_MATERIALS", bom_data), ("PURCHASE_ORDERS", po_data), ("TRADE_DATA", trade_data),
    ]
    counts = {}
    for table_name, data in datasets:
        df = pd.DataFrame(data)
        session.write_pandas(df, table_name, overwrite=False)
        counts[table_name] = len(data)

    summary = ", ".join(f"{t}: {c}" for t, c in counts.items())
    unique_consignees = len({r["CONSIGNEE_NAME"] for r in trade_data})
    return f"Generated {sum(counts.values())} rows ({summary}). Trade coverage: {unique_consignees}/{len(vendors_data)} vendors."
$$;

CALL GENERATE_SYNTHETIC_DATA(42);

--------------------------------------------------------------------------------
-- STEP 13: CREATE RISK ANALYSIS UDF
--------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION ANALYZE_RISK_SCENARIO(
    scenario_type VARCHAR,
    target_region VARCHAR DEFAULT NULL,
    target_vendor VARCHAR DEFAULT NULL,
    shock_intensity FLOAT DEFAULT 0.5
)
RETURNS OBJECT
LANGUAGE SQL
AS
$$
SELECT OBJECT_CONSTRUCT(
    'scenario_type', scenario_type,
    'target', COALESCE(target_region, target_vendor, 'all'),
    'shock_intensity', shock_intensity,
    'analysis', CASE 
        WHEN scenario_type = 'REGIONAL_DISRUPTION' THEN
            (SELECT OBJECT_CONSTRUCT(
                'affected_vendors', COUNT(DISTINCT v.VENDOR_ID),
                'avg_current_risk', ROUND(AVG(rs.RISK_SCORE), 3),
                'projected_risk', ROUND(LEAST(1.0, AVG(rs.RISK_SCORE) + (shock_intensity * 0.3)), 3),
                'recommendation', CASE 
                    WHEN COUNT(*) > 5 THEN 'High concentration risk - diversify suppliers'
                    ELSE 'Moderate exposure - monitor closely'
                END
            )
            FROM VENDORS v
            JOIN RISK_SCORES rs ON v.VENDOR_ID = rs.NODE_ID
            WHERE v.COUNTRY_CODE = target_region
            )
        WHEN scenario_type = 'VENDOR_FAILURE' THEN
            (SELECT OBJECT_CONSTRUCT(
                'vendor_name', v.NAME,
                'current_risk', rs.RISK_SCORE,
                'dependent_materials', (
                    SELECT COUNT(DISTINCT MATERIAL_ID) 
                    FROM PURCHASE_ORDERS 
                    WHERE VENDOR_ID = target_vendor
                ),
                'bottleneck_impact', COALESCE(b.IMPACT_SCORE, 0),
                'recommendation', CASE
                    WHEN rs.RISK_SCORE > 0.7 THEN 'Immediate action required - identify alternates'
                    WHEN rs.RISK_SCORE > 0.4 THEN 'Develop contingency plan'
                    ELSE 'Low priority - standard monitoring'
                END
            )
            FROM VENDORS v
            JOIN RISK_SCORES rs ON v.VENDOR_ID = rs.NODE_ID
            LEFT JOIN BOTTLENECKS b ON v.VENDOR_ID = b.NODE_ID
            WHERE v.VENDOR_ID = target_vendor
            )
        WHEN scenario_type = 'PORTFOLIO_SUMMARY' THEN
            (SELECT OBJECT_CONSTRUCT(
                'total_vendors', COUNT(DISTINCT VENDOR_ID),
                'critical_count', SUM(CASE WHEN rs.RISK_CATEGORY = 'CRITICAL' THEN 1 ELSE 0 END),
                'high_risk_count', SUM(CASE WHEN rs.RISK_CATEGORY IN ('CRITICAL', 'HIGH') THEN 1 ELSE 0 END),
                'avg_portfolio_risk', ROUND(AVG(rs.RISK_SCORE), 3),
                'total_bottlenecks', (SELECT COUNT(*) FROM BOTTLENECKS),
                'health_score', ROUND((1 - AVG(rs.RISK_SCORE)) * 100, 1)
            )
            FROM VENDORS v
            JOIN RISK_SCORES rs ON v.VENDOR_ID = rs.NODE_ID
            )
        ELSE
            OBJECT_CONSTRUCT('error', 'Unknown scenario type. Use: REGIONAL_DISRUPTION, VENDOR_FAILURE, or PORTFOLIO_SUMMARY')
    END
)
$$;

CREATE OR REPLACE PROCEDURE RUN_RISK_SCENARIO(
    scenario_type VARCHAR,
    target_region VARCHAR DEFAULT NULL,
    target_vendor VARCHAR DEFAULT NULL,
    shock_intensity FLOAT DEFAULT 0.5
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN
    LET result OBJECT := (SELECT ANALYZE_RISK_SCENARIO(:scenario_type, :target_region, :target_vendor, :shock_intensity));
    RETURN result::VARCHAR;
END;
$$;

--------------------------------------------------------------------------------
-- STEP 14: FETCH GIT REPOSITORY (for notebooks, streamlit, semantic model)
--------------------------------------------------------------------------------

ALTER GIT REPOSITORY SUPPLY_CHAIN_RISK_REPO FETCH;

--------------------------------------------------------------------------------
-- STEP 15: DEPLOY GNN NOTEBOOK
--------------------------------------------------------------------------------

COPY FILES
    INTO @MODELS_STAGE/notebooks/
    FROM @SUPPLY_CHAIN_RISK_REPO/branches/main/notebooks/
    FILES = ('gnn_supply_chain_risk.ipynb');

-- GPU Notebook (requires External Access Integration for PyTorch Geometric + cuGraph)
CREATE OR REPLACE NOTEBOOK SUPPLY_CHAIN_RISK.SUPPLY_CHAIN_RISK.SUPPLY_CHAIN_RISK_GNN_NOTEBOOK
    FROM '@MODELS_STAGE/notebooks/'
    MAIN_FILE = 'gnn_supply_chain_risk.ipynb'
    RUNTIME_NAME = 'SYSTEM$GPU_RUNTIME'
    COMPUTE_POOL = 'SUPPLY_CHAIN_RISK_COMPUTE_POOL'
    QUERY_WAREHOUSE = 'SUPPLY_CHAIN_RISK_WH'
    EXTERNAL_ACCESS_INTEGRATIONS = (SUPPLY_CHAIN_RISK_EXTERNAL_ACCESS)
    IDLE_AUTO_SHUTDOWN_TIME_SECONDS = 1800
    COMMENT = 'GNN Supply Chain Risk Analysis - PyTorch Geometric graph neural network training';

ALTER NOTEBOOK SUPPLY_CHAIN_RISK_GNN_NOTEBOOK ADD LIVE VERSION FROM LAST;

--------------------------------------------------------------------------------
-- STEP 16: UPLOAD SEMANTIC MODEL
--------------------------------------------------------------------------------

COPY FILES
    INTO @SEMANTIC_MODELS/
    FROM @SUPPLY_CHAIN_RISK_REPO/branches/main/scripts/semantic_models/
    FILES = ('supply_chain_risk_gnn.yaml');

--------------------------------------------------------------------------------
-- STEP 17: DEPLOY GNN STREAMLIT APP
--------------------------------------------------------------------------------

CREATE OR REPLACE STREAMLIT SUPPLY_CHAIN_RISK.SUPPLY_CHAIN_RISK.GNN_SUPPLY_CHAIN_RISK_APP
    FROM '@SUPPLY_CHAIN_RISK_REPO/branches/main/streamlit_gnn/'
    MAIN_FILE = 'streamlit_app.py'
    QUERY_WAREHOUSE = 'SUPPLY_CHAIN_RISK_WH'
    COMMENT = '{"origin":"sf_sit-is", "name":"supply_chain_risk_intelligence_with_snowflake", "version":{"major":1, "minor":0}}';

ALTER STREAMLIT GNN_SUPPLY_CHAIN_RISK_APP ADD LIVE VERSION FROM LAST;

--------------------------------------------------------------------------------
-- STEP 18: CREATE GNN PASS-THROUGH VIEWS
--------------------------------------------------------------------------------

CREATE OR REPLACE VIEW RISK_SCORES_GNN AS SELECT * FROM RISK_SCORES;
CREATE OR REPLACE VIEW PREDICTED_LINKS_GNN AS SELECT * FROM PREDICTED_LINKS;
CREATE OR REPLACE VIEW BOTTLENECKS_GNN AS SELECT * FROM BOTTLENECKS;

--------------------------------------------------------------------------------
-- STEP 19: CREATE CORTEX AGENT
--------------------------------------------------------------------------------

CREATE OR REPLACE AGENT SUPPLY_CHAIN_GNN_AGENT
  COMMENT = 'Supply Chain Risk Copilot (GNN) - answers questions using GNN semantic model and scenario analysis'
  FROM SPECIFICATION
  $$
  models:
    orchestration: claude-4-sonnet

  instructions:
    system: |
      You are a Supply Chain Risk Analyst powered by GNN (Graph Neural Network) insights.

      You have access to two tools:
      1. supply_chain_analytics: Use this to query supply chain data including vendors, risk scores, bottlenecks, and regional risk factors
      2. risk_scenario_analyzer: Use this to run what-if scenario analysis (regional disruptions, vendor failures, portfolio summaries)

      Guidelines:
      - For questions about risk scores, use supply_chain_analytics to query the RISK_SCORES table
      - For questions about bottlenecks or single points of failure, query the BOTTLENECKS table
      - For questions about suppliers/vendors, query the VENDORS table joined with risk data
      - For regional risk analysis, query the REGIONS table
      - For "what if" scenarios or disruption simulations, use risk_scenario_analyzer with the appropriate scenario_type:
        - REGIONAL_DISRUPTION: Assess impact of a regional event (requires target_region country code)
        - VENDOR_FAILURE: Assess impact of losing a specific vendor (requires target_vendor ID)
        - PORTFOLIO_SUMMARY: Get overall portfolio health metrics
      - Always explain the business implications of risk findings
      - Highlight critical risks and unmitigated bottlenecks as priorities

      Your goal is to help procurement and supply chain teams identify unknown risks, concentration points, and Tier-2+ dependencies before disruptions occur.
    sample_questions:
      - question: "What is our overall portfolio risk score?"
      - question: "What percentage of our suppliers are high risk?"
      - question: "Which suppliers have critical risk and where are they located?"
      - question: "Show me the top 5 bottlenecks by impact score"
      - question: "Which regions have the highest geopolitical risk?"
      - question: "What would happen if there was a disruption in China?"

  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "supply_chain_analytics"
    - tool_spec:
        type: "generic"
        name: "risk_scenario_analyzer"
        description: "Run what-if scenario analysis for regional disruptions, vendor failures, or portfolio health summaries. Use scenario_type REGIONAL_DISRUPTION with a country code, VENDOR_FAILURE with a vendor ID, or PORTFOLIO_SUMMARY for overall health."
        input_schema:
          type: object
          properties:
            scenario_type:
              type: string
              description: "One of: REGIONAL_DISRUPTION, VENDOR_FAILURE, PORTFOLIO_SUMMARY"
            target_region:
              type: string
              description: "Country code (e.g. CHN, USA, DEU) for REGIONAL_DISRUPTION scenarios"
            target_vendor:
              type: string
              description: "Vendor ID (e.g. V10001) for VENDOR_FAILURE scenarios"
            shock_intensity:
              type: number
              description: "Disruption severity from 0.0 to 1.0 (default 0.5)"
          required:
            - scenario_type

  tool_resources:
    supply_chain_analytics:
      semantic_model_file: "@SUPPLY_CHAIN_RISK.SUPPLY_CHAIN_RISK.SEMANTIC_MODELS/supply_chain_risk_gnn.yaml"
      execution_environment:
        type: "warehouse"
        warehouse: "SUPPLY_CHAIN_RISK_WH"
    risk_scenario_analyzer:
      type: "procedure"
      identifier: "SUPPLY_CHAIN_RISK.SUPPLY_CHAIN_RISK.RUN_RISK_SCENARIO"
      execution_environment:
        type: "warehouse"
        name: "SUPPLY_CHAIN_RISK_WH"
  $$;

ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT
  ADD AGENT SUPPLY_CHAIN_GNN_AGENT;

--------------------------------------------------------------------------------
-- SETUP COMPLETE
--------------------------------------------------------------------------------

SELECT 'GNN Supply Chain Risk Analysis (GNN-Only) - Setup Complete!' as STATUS;

/******************************************************************************
 * SETUP COMPLETE!
 * 
 * Your GNN Supply Chain Risk Analysis platform is ready with:
 * - Database: SUPPLY_CHAIN_RISK
 * - Warehouse: SUPPLY_CHAIN_RISK_WH
 * - Compute Pool: SUPPLY_CHAIN_RISK_COMPUTE_POOL (GPU_NV_S)
 * - Tables: 6 input + 3 GNN output = 9 tables
 * - Views: 4 analytics + 3 GNN pass-through = 7 views
 * - GNN Notebook: SUPPLY_CHAIN_RISK_GNN_NOTEBOOK (GPU, PyTorch Geometric)
 * - GNN Streamlit: GNN_SUPPLY_CHAIN_RISK_APP
 * - GNN Agent: SUPPLY_CHAIN_GNN_AGENT → semantic model on _GNN views
 * - UDF: ANALYZE_RISK_SCENARIO
 * 
 * NEXT STEPS:
 * 1. Open the GNN notebook in Snowsight and run all cells to train the GNN
 *    and populate risk scores, predicted links, and bottleneck tables.
 *    The notebook automatically switches to SUPPLY_CHAIN_RISK_ROLE so all
 *    output stays owned by the demo role (no ACCOUNTADMIN dependency).
 * 2. Open the Streamlit dashboard to explore results
 * 3. Chat with the Cortex Agent for natural language risk analysis
 * 
 * To remove everything: Run scripts/teardown.sql
 ******************************************************************************/
