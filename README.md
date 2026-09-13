# PROVISYN — Supply Chain Risk, Resilience & Decision Intelligence

> **Predict disruption. Quantify impact. Simulate decisions. Build resilience.**  
> *Built & Engineered by Ravi Ranjan*  
> *Based on Snowflake Labs' [sfguide-supply-chain-risk-intelligence-with-snowflake](https://github.com/Snowflake-Labs/sfguide-supply-chain-risk-intelligence-with-snowflake) (Apache-2.0, Copyright Snowflake Inc.)*

---

## What You Will Build

- A GPU-accelerated notebook that trains a GraphSAGE model on supply chain data
- Risk scores propagated through multi-tier supplier networks
- Predicted unknown Tier-2+ dependencies via link prediction
- Identified bottlenecks and single points of failure
- A Cortex Agent for natural language supply chain queries
- A multi-page Streamlit dashboard for risk visualization and mitigation planning

## What You Will Learn

- How to train Graph Neural Networks using PyTorch Geometric in Snowflake Notebooks
- How to use GPU compute pools for ML workloads
- How to create a Cortex Agent with semantic models
- How to build multi-page Streamlit dashboards in Snowflake
- How to apply GNN techniques (message passing, link prediction) to supply chain risk

## Prerequisites

- Snowflake account with ACCOUNTADMIN role
- Cortex AI features enabled

**For GPU Notebook (Option A):**
- GPU compute pool support (GPU_NV_S instance family)
- External Access Integration support (**not available on trial accounts**)

**For NetworkX Notebook (Option B):**
- No additional requirements — works on any Snowflake account

## Quick Start

### Step 1: Run Setup

1. Open Snowsight: **Projects** → **Worksheets**
2. Click **+** to create a new SQL worksheet
3. Choose your path:
   - **GNN (requires EAI + GPU):** Copy [`scripts/setup_gnn.sql`](https://github.com/Snowflake-Labs/sfguide-supply-chain-risk-intelligence-with-snowflake/blob/main/scripts/setup_gnn.sql)
   - **NetworkX (trial-friendly):** Copy [`scripts/setup_networkx.sql`](https://github.com/Snowflake-Labs/sfguide-supply-chain-risk-intelligence-with-snowflake/blob/main/scripts/setup_networkx.sql)
4. Paste and click **Run All**

### Step 2: Run a Notebook

Two notebook options are available:

#### Option A: GPU Notebook (Full GNN — requires EAI)

1. Navigate: **Projects** → **Notebooks** → `SUPPLY_CHAIN_RISK_GNN_NOTEBOOK`
2. Set your role to `SUPPLY_CHAIN_RISK_ROLE` (top-right role selector)
3. Click **Run All**

The GPU notebook will:
- Install PyTorch Geometric + cuGraph via pip (requires External Access Integration)
- Build a heterogeneous graph from ERP and trade data
- Train a GraphSAGE model for risk propagation and link prediction
- Run GPU-accelerated graph analytics (PageRank, Louvain, betweenness)
- Write results to RISK_SCORES, PREDICTED_LINKS, and BOTTLENECKS tables (GNN schema)

#### Option B: NetworkX Notebook (No EAI required)

1. Navigate: **Projects** → **Notebooks** → `SUPPLY_CHAIN_RISK_NX_NOTEBOOK`
2. Set your role to `SUPPLY_CHAIN_RISK_ROLE` (top-right role selector)
3. Click **Run All**

The NetworkX notebook will:
- Use only Snowflake conda channel packages (no external access)
- Run CPU-based graph analytics (PageRank, Louvain, betweenness)
- Use Jaccard similarity for link prediction (instead of GNN)
- Write results to NX_RISK_SCORES, NX_PREDICTED_LINKS, and NX_BOTTLENECKS tables (NX schema)

> **Note:** Each notebook writes to its own output tables. Compatibility views (_GNN and _NX suffixed) normalize the schemas so each Streamlit app works with its respective notebook output.

### Step 3: Access the Dashboard

> **Note:** Run a notebook first (Step 2) to populate risk scores, predicted links, and bottlenecks. The dashboard will show empty data without notebook execution.

Navigate: **Projects** → **Streamlit** → `GNN_SUPPLY_CHAIN_RISK_APP` (GNN path) or `NX_SUPPLY_CHAIN_RISK_APP` (NetworkX path)

| Page | Description |
|------|-------------|
| **Executive Summary** | High-level risk overview with KPIs and health score |
| **Exploratory Analysis** | Deep-dive into vendor and material risk distributions |
| **Supply Network** | Interactive graph visualization of the supply chain |
| **Tier 2 Analysis** | Predicted unknown dependencies and evidence strength |
| **Scenario Simulator** | What-if analysis for regional disruptions and vendor failures |
| **Command Center** | Cortex Agent chat for natural language risk queries |
| **Risk Mitigation** | Prioritized action items and mitigation strategies |
| **About** | Architecture and methodology documentation |

### Step 4: Chat with the Agent

Navigate: **Snowflake Intelligence** → `SUPPLY_CHAIN_GNN_AGENT` (GNN) or `SUPPLY_CHAIN_NX_AGENT` (NetworkX)

The agent comes with preconfigured sample prompts. Try questions like:

```
What is our overall portfolio risk score?
```

```
Which suppliers have critical risk and where are they located?
```

```
Show me the top 5 bottlenecks by impact score
```

```
What is the average risk score by country?
```

```
Which regions have the highest geopolitical risk?
```

```
What would happen if there was a disruption in China?
```

```
Simulate a vendor failure for V10001 with high severity
```

```
What if Australia had a major natural disaster — which suppliers are affected?
```

```
Run a portfolio summary and tell me our overall health score
```

```
What is the projected risk if we lose all suppliers in South Korea?
```

## Synthetic Data Generation

Setup generates realistic supply chain data automatically via a Snowpark Python stored procedure — no CSVs or external files required. Both setup scripts call `GENERATE_SYNTHETIC_DATA(42)`, which creates:

| Table | Description |
|-------|-------------|
| `REGIONS` | Global manufacturing regions with geopolitical risk scores and regulatory complexity |
| `VENDORS` | Tiered suppliers (Tier-1/2/3) across 7 categories: electronics, chemicals, metals, automotive, semiconductor, logistics, raw materials |
| `MATERIALS` | Finished goods, semi-finished, and raw materials with criticality ratings |
| `BILL_OF_MATERIALS` | Multi-level BOM relationships linking finished → semi-finished → raw materials |
| `PURCHASE_ORDERS` | Vendor-material orders with region-affinity weighting and realistic pricing |
| `TRADE_DATA` | Customs/shipping records with HS codes, ports, and Tier-2 supplier routing patterns |

## What Gets Created

- **Database:** `SUPPLY_CHAIN_RISK`
- **Schema:** `SUPPLY_CHAIN_RISK`
- **Warehouse:** `SUPPLY_CHAIN_RISK_WH`
- **Role:** `SUPPLY_CHAIN_RISK_ROLE`
- **Compute Pool:** `SUPPLY_CHAIN_RISK_COMPUTE_POOL` (GPU_NV_S) — GNN only
- **Tables:** Input ERP tables + model output tables
- **Views:** Analytics views + pass-through (GNN) or compatibility (NX) views
- **Notebooks:** `SUPPLY_CHAIN_RISK_GNN_NOTEBOOK`, `SUPPLY_CHAIN_RISK_NX_NOTEBOOK`
- **Streamlit:** `GNN_SUPPLY_CHAIN_RISK_APP`, `NX_SUPPLY_CHAIN_RISK_APP`
- **Agents:** `SUPPLY_CHAIN_GNN_AGENT`, `SUPPLY_CHAIN_NX_AGENT`
- **Stored Procedures:** `GENERATE_SYNTHETIC_DATA`, `RUN_RISK_SCENARIO`
- **UDF:** `ANALYZE_RISK_SCENARIO`
- **Semantic Models:** `supply_chain_risk_gnn.yaml`, `supply_chain_risk_nx.yaml`

## Cleanup

1. Open Snowsight: **Projects** → **Worksheets**
2. Create a new SQL worksheet
3. Copy contents of [`scripts/teardown.sql`](https://github.com/Snowflake-Labs/sfguide-supply-chain-risk-intelligence-with-snowflake/blob/main/scripts/teardown.sql)
4. Click **Run All**

## Repository Structure

```
├── notebooks/
│   ├── gnn_supply_chain_risk.ipynb                  # GPU: PyTorch Geometric + cuGraph
│   ├── graphsage_supply_chain_risk.ipynb            # CPU: NetworkX (no EAI)
│   ├── environment.yml                               # Conda packages for GNN notebook
│   └── graphsage_supply_chain_risk_environment.yml  # Conda packages for NetworkX notebook
├── scripts/
│   ├── setup_gnn.sql            # GNN path (EAI + GPU required)
│   ├── setup_networkx.sql       # NetworkX path (trial-friendly)
│   ├── teardown.sql             # Cleanup script (works for both)
│   └── semantic_models/
│       ├── supply_chain_risk_gnn.yaml   # GNN semantic model
│       └── supply_chain_risk_nx.yaml    # NetworkX semantic model
├── streamlit_gnn/               # GNN Streamlit app
│   ├── streamlit_app.py
│   ├── environment.yml
│   ├── snowflake.yml
│   ├── assets/
│   ├── components/
│   ├── utils/
│   └── pages/
├── streamlit_networkx/          # NetworkX Streamlit app
│   ├── streamlit_app.py
│   ├── environment.yml
│   ├── snowflake.yml
│   ├── assets/
│   ├── utils/
│   └── pages/
└── README.md
```

## Conclusion

You now have a complete GNN-powered supply chain risk intelligence platform that:

- Trains Graph Neural Networks with PyTorch Geometric on GPU-accelerated Snowflake Notebooks
- Propagates risk scores through multi-tier supplier networks via GraphSAGE message passing
- Discovers unknown Tier-2+ dependencies using link prediction on trade data patterns
- Identifies single points of failure and concentration risks before disruptions occur
- Enables natural language risk analysis via Cortex Agent with semantic model
- Delivers actionable insights through a multi-page Streamlit dashboard

Transform your supply chain from reactive firefighting to proactive resilience.

## License

Copyright (c) Snowflake Inc. All rights reserved. Licensed under [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0).
