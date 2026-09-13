"""Configuration settings for PROVISYN."""
import os
from pathlib import Path
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseModel):
    APP_NAME: str = "PROVISYN"
    APP_FULL_NAME: str = "PROVISYN — Supply Chain Risk, Resilience & Decision Intelligence"
    TAGLINE: str = "Predict disruption. Quantify impact. Simulate decisions. Build resilience."
    AUTHOR: str = "Built & Engineered by Ravi Ranjan"
    FOUNDATION: str = "Based on Snowflake Labs sfguide-supply-chain-risk-intelligence-with-snowflake (Apache-2.0, Copyright Snowflake Inc.)"
    
    DATA_BACKEND: str = Field(default_factory=lambda: os.getenv("PROVISYN_DATA_BACKEND", "duckdb").lower())
    GRAPH_BACKEND: str = Field(default_factory=lambda: os.getenv("PROVISYN_GRAPH_BACKEND", "networkx").lower())
    DUCKDB_PATH: str = Field(default_factory=lambda: os.getenv("PROVISYN_DUCKDB_PATH", str(ROOT_DIR / "provisyn.duckdb")))
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("PROVISYN_LOG_LEVEL", "INFO"))
    
    # Snowflake config (optional, used if DATA_BACKEND == 'snowflake')
    SNOWFLAKE_ROLE: str = Field(default_factory=lambda: os.getenv("SNOWFLAKE_ROLE", "SUPPLY_CHAIN_RISK_ROLE"))
    SNOWFLAKE_WAREHOUSE: str = Field(default_factory=lambda: os.getenv("SNOWFLAKE_WAREHOUSE", "SUPPLY_CHAIN_RISK_WH"))
    SNOWFLAKE_DATABASE: str = Field(default_factory=lambda: os.getenv("SNOWFLAKE_DATABASE", "SUPPLY_CHAIN_RISK"))
    SNOWFLAKE_SCHEMA: str = Field(default_factory=lambda: os.getenv("SNOWFLAKE_SCHEMA", "SUPPLY_CHAIN_RISK"))

settings = Settings()
