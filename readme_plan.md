# readme_plan.md

Final `README.md` structure (all 24 items from Part 20), to be written in Phase 19 once content is
accurate:

1. **PROVISYN overview** — name, tagline ("Predict disruption. Quantify impact. Simulate
   decisions. Build resilience."), one-paragraph description.
2. **Problem statement** — the "illusion of diversity" / hidden Tier-2+ dependency problem
   (genuinely inherited insight from the source repo's storytelling, kept because it's accurate,
   not because it's decorative).
3. **Product philosophy** — the Risk → Cause → Cascade → Impact → Intervention → Simulation →
   Optimization → Decision journey (Part 6).
4. **Features** — pulled directly from the final state of `features.md` after implementation
   (only features actually shipped, each marked if "planned"/optional where relevant).
5. **Architecture** — diagram + summary from `architecture.md`.
6. **Data pipeline** — summary from `data_model.md`/`architecture.md`.
7. **ML pipeline** — summary from `ml_graph_risk_forecasting.md`.
8. **Graph intelligence** — summary, explicitly noting NetworkX is the default, GNN is optional.
9. **Cascade engine** — summary from `decision_engines.md`.
10. **Financial exposure** — summary, with the observed/calculated/simulated/assumption labeling
    convention documented so users interpret numbers correctly.
11. **Resilience Lab** — summary, scenario types list.
12. **Optimization** — summary, technology used (PuLP/OR-Tools), what it does and doesn't cover.
13. **Explainable AI** — summary, SHAP usage.
14. **Copilot** — tool list, grounding guarantee ("never states a number that didn't come from a
    tool call").
15. **Tech stack** — table from `tech_stack.md`.
16. **Installation** — local (DuckDB, `pip install -r requirements.txt`) and Snowflake
    (`database/snowflake/setup_*.sql`) paths, both documented since both are real.
17. **Local setup** — step-by-step for the DuckDB/local path (new; the source repo has no local
    path today).
18. **Usage** — how to run the Streamlit app, run a scenario, chat with the Copilot.
19. **Project structure** — the tree from `architecture.md`.
20. **Testing** — `pytest` invocation, what's covered.
21. **Screenshots** — captured once the redesigned UI exists (placeholder note until then, never a
    fabricated/mocked screenshot).
22. **Attribution** — summary of `attribution_plan.md`; explicit acknowledgment that this project
    is built on Snowflake Inc.'s Apache-2.0-licensed `sfguide-supply-chain-risk-intelligence-with-
    snowflake` quickstart, with a link to the original repository.
23. **License** — Apache 2.0 (inherited; PROVISYN's new original code may additionally carry a
    `Copyright © 2026 Ravi Ranjan` header, but the project as a whole remains Apache-2.0-licensed
    since it is a derivative work — a derivative cannot silently relicense the inherited portions).
24. **Author** — "Built & Engineered by Ravi Ranjan," with the foundation credit from #22
    immediately alongside it, never separated in a way that could look like independent origin.
