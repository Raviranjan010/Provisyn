# PROVISYN — Supply Chain Risk, Resilience & Decision Intelligence

> **Predict disruption. Quantify impact. Simulate decisions. Build resilience.**  
> *Built & Engineered by Ravi Ranjan*  
> *Based on Snowflake Labs' [sfguide-supply-chain-risk-intelligence-with-snowflake](https://github.com/Snowflake-Labs/sfguide-supply-chain-risk-intelligence-with-snowflake) (Apache-2.0, Copyright Snowflake Inc.)*

---

## 1. PROVISYN Overview

**PROVISYN** is an enterprise-grade, multi-tier supply chain decision intelligence system. It quantifies vulnerability, maps multi-tier supplier networks, models upstream disruption blast radiuses, forecasts inventory stockouts, and solves optimal capital allocation budgets to build resilient global supply chains.

PROVISYN operates seamlessly across a dual-engine architecture:
- **Local Embedded Mode**: Zero-cloud, instant setup powered by **DuckDB**, **NetworkX**, and local Python ML engines.
- **Enterprise Cloud Mode**: Massive-scale analytics powered by **Snowflake**, **Cortex AI**, and optional GPU Graph Neural Networks (GNNs).

---

## 2. Problem Statement: The Illusion of Diversity

In modern supply chain management, organizations frequently maintain what appears to be a diversified Tier-1 supplier portfolio across hundreds of vendors. However, deep-tier structural audits reveal that separate Tier-1 vendors often depend on the exact same Tier-2 refiners, Tier-3 smelters, or single-source regional mineral extractors. 

When an unforeseen geopolitical, port, or environmental disruption strikes an upstream node, Tier-1 suppliers fail simultaneously. PROVISYN shatters this "illusion of diversity" by mining hidden dependencies, uncovering single points of failure (SPOFs), and simulating multi-echelon cascading failure paths before disruptions occur.

---

## 3. Product Philosophy

PROVISYN is designed around the continuous **Risk-to-Decision Journey**:

$$\text{Risk} \longrightarrow \text{Cause} \longrightarrow \text{Cascade} \longrightarrow \text{Impact} \longrightarrow \text{Intervention} \longrightarrow \text{Simulation} \longrightarrow \text{Optimization} \longrightarrow \text{Decision}$$

1. **Quantify Risk**: Multi-dimensional scoring across financial, operational, geopolitical, and network dimensions.
2. **Diagnose Cause**: Uncover root causes via link prediction and SHAP feature attribution.
3. **Trace Cascade**: Simulate upstream-to-downstream failure propagation through Bills of Materials (BOM).
4. **Quantify Impact**: Measure revenue-at-risk, production losses, and inventory holding penalties with strict mathematical transparency.
5. **Formulate Interventions**: Propose concrete mitigations (buffer inventory, dual-sourcing, supplier qualification).
6. **Simulate Scenarios**: Stress-test digital twins using Monte Carlo shock scenarios.
7. **Optimize Portfolios**: Solve linear programming formulations under capital budget constraints.
8. **Decide with Confidence**: Actionable briefings, alerts, and tool-grounded conversational intelligence.

---

## 4. Features & Capabilities

- **Command Overview**: Operational cockpit with live resilience indicators, financial exposure, critical entity counts, and real-time alerts.
- **Multi-Tier Risk Intelligence**: 10-dimensional risk assessment scoring vendors and materials with graph-propagated and supervised regression scores.
- **Graph Topology & Network Intelligence**: PageRank centrality, betweenness analysis, and Louvain community clustering.
- **Hidden Dependencies Detection**: Uncover undisclosed Tier-2+ supplier links using Jaccard trade-counterparty overlap and graph embeddings.
- **Supplier 360 Intelligence**: Detailed profiles, reliability scores, capacity monitoring, and concentration risk metrics.
- **Financial Exposure Engine**: Verifiable revenue-at-risk, production loss modeling, expediting freight markup, and expected loss.
- **Demand & Inventory Intelligence**: Dynamic risk-aware safety stock sizing ($ROP = d \cdot L + SS_{risk}$) and logistic stockout probability.
- **Resilience Lab & Digital Twin**: Scenario simulation framework evaluating shock duration, entity curtailment, and before/after resilience gains.
- **Prescriptive Recommendations**: PuLP-powered knapsack and linear programming optimizing mitigation portfolios under capital expenditure budgets.
- **PROVISYN Copilot**: Tool-grounded decision assistant strictly referencing engine outputs with monospace source attribution.
- **Model Intelligence & Governance**: Model registry tracking PR-AUC, F1, Accuracy, training dataset seeds, and drift status.
- **Alerts & Events Management**: Persisted operational event feed with automated threshold triggers.
- **Executive Resilience Reports**: One-click auditable briefing generation synthesizing risk, exposure, cascades, and recommendations.

---

## 5. System Architecture

PROVISYN follows a clean modular hexagonal architecture separating data backends, graph backends, computational engines, ML pipelines, and presentation interfaces:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   STREAMLIT PRESENTATION LAYER (14 PAGES)              │
│   Command • Risk • Network • Dependencies • Supplier • Financial       │
│   Inventory • Resilience • Recs • Copilot • Models • Alerts • Reports  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                    PROVISYN COPILOT & AGENT LAYER                      │
│            backend/copilot/tools.py  •  backend/copilot/agent.py       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────┴────────────────────────────────────┐
│                       DECISION & ANALYTICAL ENGINES                    │
│   RiskEngine        • CascadeEngine     • FinancialExposureEngine      │
│   SPOFEngine        • InventoryEngine   • OptimizationEngine           │
│   SimulationEngine  • ResilienceEngine  • RecommendationEngine         │
└──────────────┬──────────────────────────────────────────┬──────────────┘
               │                                          │
┌──────────────┴──────────────┐            ┌──────────────┴──────────────┐
│       GRAPH LAYER           │            │    ML & PREDICTIVE LAYER    │
│  NetworkX (Default local)   │            │  Tabular Risk Model (XGB)   │
│  PyTorch GNN (Optional GPU) │            │  SHAP Explainability        │
│  backend/graph/analytics.py │            │  Demand / Stockout Forecast │
└──────────────┬──────────────┘            └──────────────┬──────────────┘
               │                                          │
┌──────────────┴──────────────────────────────────────────┴──────────────┐
│                    DATA LAYER REPOSITORY (DUAL BACKEND)                │
│         DuckDB (Default Local)      │     Snowflake (Cloud Cortex)     │
│             provisyn.duckdb         │      Snowpark / Snowsight        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Data Pipeline & Schema

PROVISYN establishes an auditable relational data schema (`database/schema.sql`):

- **Master Data**: `VENDORS`, `MATERIALS`, `PURCHASE_ORDERS`, `BILL_OF_MATERIALS`, `TRADE_DATA`, `REGIONS`, `PRODUCTS`, `FACTORIES`, `ORDERS`, `INVENTORY`, `SHIPMENTS`.
- **Graph & Risk Tables**: `RISK_SCORES`, `PREDICTED_LINKS`, `BOTTLENECKS`, `RISK_HISTORY`, `DISRUPTIONS`.
- **Decision Intelligence Tables**: `SCENARIOS`, `SIMULATION_RUNS`, `INTERVENTIONS`, `RECOMMENDATIONS`, `ALERTS`, `DECISION_HISTORY`, `MODEL_VERSIONS`, `FORECASTS`.

All tables are read and written through the unified `BaseRepository` interface (`backend/data/repository.py`), supporting seamless switching between DuckDB and Snowflake.

---

## 7. Machine Learning Pipeline

1. **Tabular Risk Model (`ml/risk/`)**:
   - Supervised regression and classification evaluating financial health, reliability, delivery track records, tier depth, and graph centrality.
   - Evaluated on clean train/test splits reporting PR-AUC, F1-score, accuracy, and RMSE.
2. **Model Explainability (`ml/evaluation/`)**:
   - SHAP (SHapley Additive exPlanations) values computed for individual entity risk factors.
   - Transparently highlights top positive and negative risk drivers.
3. **Forecasting Engine (`ml/forecasting/`)**:
   - Lead time and demand forecast models predicting upcoming stockout risks across supply corridors.
4. **Model Registry (`MODEL_VERSIONS`)**:
   - Strictly governed model metadata table ensuring no fabricated performance statistics are presented.

---

## 8. Graph Intelligence

- **Default Engine**: Pure Python NetworkX graph analytics (`backend/graph/analytics.py`). Computes PageRank, betweenness centrality, and Louvain community partitions.
- **Hidden Links**: Jaccard counterparty overlap over global trade flows (`TRADE_DATA`) identifying undisclosed Tier-2 relationships.
- **Single Points of Failure**: Combines centrality rankings with alternative-route path counts to classify critical bottlenecks.
- **Optional GNN Track (`ml/graph/gnn_optional/`)**: GraphSAGE heterogeneous message-passing architecture ported from Snowflake GPU notebooks, activated via `PROVISYN_GRAPH_BACKEND=gnn`.

---

## 9. Cascade Engine

The Cascade Disruption Engine (`backend/engines/cascade.py`) executes multi-hop breadth-first traversal across graph edges:
$$\text{Disrupted Vendor} \xrightarrow{\text{SUPPLIES}} \text{Material} \xrightarrow{\text{BOM}} \text{Sub-Assembly} \xrightarrow{\text{PRODUCES}} \text{Factory} \xrightarrow{\text{FULFILLS}} \text{Customer Order}$$

Configurable attenuation parameters dampen disruption severity across tiers, preventing unrealistic shock inflation while revealing true downstream blast radiuses.

---

## 10. Financial Exposure Engine

Financial exposure is computed with explicit data labels per Part 25:
- **Revenue at Risk** *(simulated)*: Total contract value of delayed or canceled customer orders.
- **Production Loss** *(calculated)*: Curtailed manufacturing capacity valued at unit sale price.
- **Holding Costs** *(calculated)*: Holding fees for idle WIP inventory awaiting blocked components.
- **Expediting Costs** *(assumption)*: 15% freight and express supplier surcharge.
- **Expected Loss** *(calculated)*: $\text{Total Exposure} \times \text{Disruption Probability}$.

---

## 11. Resilience Lab & Digital Twin

The Resilience Lab simulates what-if scenarios (regional port embargoes, supplier solvency failures, raw material export bans).
- **Composite Resilience Score**: Weighted across Redundancy (25%), Risk Hedging (25%), Buffer Coverage (25%), and Exposure Containment (25%).
- **Intervention ROI**: Models resilience gains ($\Delta R$) per dollar spent on mitigations.

---

## 12. Prescriptive Optimization

Powered by PuLP integer linear programming (`backend/engines/optimization.py`):
$$\max \sum_{i \in \text{Actions}} \left( \text{RiskReduction}_i + \text{ResilienceGain}_i \right) \cdot x_i$$
$$\text{subject to} \sum_{i \in \text{Actions}} \text{Cost}_i \cdot x_i \le \text{Budget}, \quad x_i \in \{0, 1\}$$

Ranks candidates and yields optimal mitigation action plans under hard budget caps.

---

## 13. Explainable AI (XAI)

PROVISYN refuses "black-box" risk scoring. For any high-risk supplier or material:
- **Tabular Drivers**: SHAP value decompositions show exact point additions or subtractions (e.g. *Delivery Delay: +18 pts*, *Financial Ratio: -8 pts*).
- **Graph Structural Drivers**: Multi-hop dependency paths pinpoint why an upstream regional vulnerability affects a downstream factory.

---

## 14. PROVISYN Copilot

A tool-grounded conversational intelligence agent:
- Grounded in 7 backend engine tools (`risk_engine`, `graph_engine`, `cascade_engine`, `financial_engine`, `simulation_engine`, `optimization_engine`, `inventory_engine`).
- Strict anti-hallucination guarantee: **Every number in an assistant response traces directly to a tool invocation in that turn.**
- Monospace source labels: Every metric is stamped with `source: <engine>` in the UI.

---

## 15. Technology Stack

| Layer | Component | Technologies |
|---|---|---|
| **Frontend UI** | 14-page Interactive Cockpit | Streamlit, Plotly, Custom Clean Charcoal Design System |
| **Data Engine** | Dual Local / Cloud Data Layer | DuckDB (default local), Snowflake Snowpark (cloud) |
| **Graph Layer** | Topology & Centrality | NetworkX (default local), PyTorch Geometric / GraphSAGE (GNN track) |
| **Machine Learning** | Supervised Risk & Explainability | Scikit-Learn, XGBoost, SHAP |
| **Optimization** | Prescriptive Knapsack Solver | PuLP (Linear Programming) |
| **Copilot** | Tool Orchestrator | Python Tool Dispatcher, Snowflake Cortex Agent support |
| **Testing** | Automated Quality Assurance | Pytest (Unit, Design Rule, and Pipeline Integration) |

---

## 16. Installation

PROVISYN supports both a **100% Local Python Setup** (no cloud account or credit card required) and a **Snowflake Enterprise Setup**.

### System Requirements
- Python 3.10, 3.11, or 3.12
- Git

Clone the repository:
```bash
git clone https://github.com/Raviranjan010/Provisyn.git
cd Provisyn
```

---

## 17. Local Setup (DuckDB Path)

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize and Seed the Local Database**:
   ```bash
   python scripts/seed_data.py
   ```
   *This initializes `provisyn.duckdb`, creates all relational tables, seeds the realistic "Outback Lithium" multi-tier supply chain scenario, trains the tabular risk model, and records authentic metrics in `MODEL_VERSIONS`.*

3. **Launch the PROVISYN Cockpit**:
   ```bash
   streamlit run frontend/streamlit_app.py
   ```
   Open your browser to `http://localhost:8501`.

---

## 18. Snowflake Enterprise Setup (Cloud Path)

To run PROVISYN against Snowflake:

1. Configure environment variables in `.env` or your shell:
   ```bash
   export PROVISYN_DATA_BACKEND=snowflake
   export SNOWFLAKE_ACCOUNT=<your_account>
   export SNOWFLAKE_USER=<your_username>
   export SNOWFLAKE_PASSWORD=<your_password>
   export SNOWFLAKE_ROLE=SUPPLY_CHAIN_RISK_ROLE
   export SNOWFLAKE_WAREHOUSE=SUPPLY_CHAIN_RISK_WH
   export SNOWFLAKE_DATABASE=SUPPLY_CHAIN_RISK
   export SNOWFLAKE_SCHEMA=SUPPLY_CHAIN_RISK
   ```
2. Execute the setup SQL worksheets in `database/snowflake/`:
   - `setup_networkx.sql` (or `setup_gnn.sql` for Cortex/GPU setups)
3. Launch Streamlit:
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

---

## 19. Project Structure

```
Provisyn/
├── LICENSE                             # Apache License 2.0
├── NOTICE                              # Legal attribution notice
├── LEGAL.md                            # Snowflake terms disclaimer
├── README.md                           # Comprehensive product documentation
├── requirements.txt                    # Project dependency manifest
├── database/
│   ├── schema.sql                      # Unified portable DDL schema
│   └── snowflake/                      # Snowflake setup & agent scripts
├── backend/
│   ├── core/                           # Config, database connection, logging
│   ├── data/                           # BaseRepository, DuckDB, Snowflake, generator
│   ├── graph/                          # NetworkX graph analytics & topology
│   ├── engines/                        # Risk, Cascade, Financial, SPOF, Inventory,
│   │                                   # Resilience, Simulation, Optimization, Recs
│   └── copilot/                        # Copilot tools and agent orchestrator
├── ml/
│   ├── risk/                           # Scikit-Learn/XGBoost tabular risk model
│   ├── evaluation/                     # SHAP explainability engine
│   ├── forecasting/                    # Demand and inventory forecasting
│   └── graph/gnn_optional/             # Optional GraphSAGE PyTorch Geometric port
├── frontend/
│   ├── streamlit_app.py                # Page 1: Command Overview
│   ├── components/                     # KPI, alerts, styles, and badges
│   ├── utils/                          # Navigation and layout utilities
│   └── pages/                          # Pages 2 through 14
├── scripts/
│   └── seed_data.py                    # Database seeding and model training script
└── tests/
    ├── unit/                           # Engine and design rule unit tests
    └── integration/                    # End-to-end data and simulation pipeline tests
```

---

## 20. Testing & Verification

Run the entire test suite using `pytest`:

```bash
# Run all unit tests
python -m pytest tests/unit/

# Run end-to-end integration tests
python -m pytest tests/integration/

# Validate UI design system compliance (no gradients, no blue status, 14 pages)
python -m pytest tests/unit/test_ui_design_rules.py
```

---

## 21. User Interface & Screenshots

The PROVISYN interface adheres to a high-density, professional design language:
- **Palette**: Dark charcoal `#1A1A1A` background, card surface `#242426`, subtle border `#3A3A3C`.
- **Typography**: Clean monospace numeric hierarchy with distinct status badges (Healthy `#22C55E`, Warning `#EAB308`, High `#F97316`, Critical `#EF4444`).
- **Data Provenance**: Explicit stamp tags (`observed`, `calculated`, `simulated`, `assumption`) on all metrics.

---

## 22. Attribution & Provenance

This project is built on the foundational ideas, data schemas, and graph modeling concepts from Snowflake Inc.'s open-source quickstart:

**[sfguide-supply-chain-risk-intelligence-with-snowflake](https://github.com/Snowflake-Labs/sfguide-supply-chain-risk-intelligence-with-snowflake)**  
*Copyright © Snowflake Inc. Licensed under the Apache License, Version 2.0.*

PROVISYN significantly extends the original work by introducing a portable dual-backend data layer (DuckDB + Snowflake), 11 specialized decision engines, prescriptive linear optimization, SHAP tabular explainability, inventory risk dynamics, and a tool-grounded decision intelligence Copilot.

---

## 23. License

PROVISYN is licensed under the **Apache License, Version 2.0**. See [LICENSE](file:///d:/Temp/Provisyn/LICENSE) for the full license text and [NOTICE](file:///d:/Temp/Provisyn/NOTICE) for attribution details.

---

## 24. Author & Engineering Credit

**Built & Engineered by Ravi Ranjan**  
*In conjunction with the foundational architecture of the Snowflake Labs Supply Chain Risk Intelligence quickstart.*
