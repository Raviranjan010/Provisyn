"""Repository layer supporting both DuckDB (local) and Snowflake (cloud)."""
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List
import pandas as pd
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.core.database import DatabaseManager

logger = get_logger(__name__)

class BaseRepository(ABC):
    """Abstract base repository defining the unified data access interface."""

    @abstractmethod
    def get_table(self, table_name: str) -> pd.DataFrame:
        """Fetch an entire table as a DataFrame. Returns empty DataFrame on failure."""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Execute a query and return results as DataFrame. Returns empty DataFrame on failure."""
        pass

    @abstractmethod
    def write_table(self, df: pd.DataFrame, table_name: str, overwrite: bool = False) -> bool:
        """Write DataFrame to the specified table."""
        pass

    # Core master data getters
    def get_vendors(self) -> pd.DataFrame:
        return self.get_table("VENDORS")

    def get_materials(self) -> pd.DataFrame:
        return self.get_table("MATERIALS")

    def get_purchase_orders(self) -> pd.DataFrame:
        return self.get_table("PURCHASE_ORDERS")

    def get_bill_of_materials(self) -> pd.DataFrame:
        return self.get_table("BILL_OF_MATERIALS")

    def get_trade_data(self) -> pd.DataFrame:
        return self.get_table("TRADE_DATA")

    def get_regions(self) -> pd.DataFrame:
        return self.get_table("REGIONS")

    def get_products(self) -> pd.DataFrame:
        return self.get_table("PRODUCTS")

    def get_factories(self) -> pd.DataFrame:
        return self.get_table("FACTORIES")

    def get_orders(self) -> pd.DataFrame:
        return self.get_table("ORDERS")

    def get_inventory(self) -> pd.DataFrame:
        return self.get_table("INVENTORY")

    def get_shipments(self) -> pd.DataFrame:
        return self.get_table("SHIPMENTS")

    # Risk & graph outputs
    def get_risk_scores(self) -> pd.DataFrame:
        return self.get_table("RISK_SCORES")

    def get_predicted_links(self) -> pd.DataFrame:
        return self.get_table("PREDICTED_LINKS")

    def get_bottlenecks(self) -> pd.DataFrame:
        return self.get_table("BOTTLENECKS")

    def get_risk_history(self) -> pd.DataFrame:
        return self.get_table("RISK_HISTORY")

    def get_disruptions(self) -> pd.DataFrame:
        return self.get_table("DISRUPTIONS")

    # Decision intelligence entities
    def get_scenarios(self) -> pd.DataFrame:
        return self.get_table("SCENARIOS")

    def get_simulation_runs(self) -> pd.DataFrame:
        return self.get_table("SIMULATION_RUNS")

    def get_interventions(self) -> pd.DataFrame:
        return self.get_table("INTERVENTIONS")

    def get_recommendations(self) -> pd.DataFrame:
        return self.get_table("RECOMMENDATIONS")

    def get_alerts(self) -> pd.DataFrame:
        return self.get_table("ALERTS")

    def get_decision_history(self) -> pd.DataFrame:
        return self.get_table("DECISION_HISTORY")

    def get_model_versions(self) -> pd.DataFrame:
        return self.get_table("MODEL_VERSIONS")

    def get_forecasts(self) -> pd.DataFrame:
        return self.get_table("FORECASTS")

    def get_external_risk_events(self) -> pd.DataFrame:
        return self.get_table("EXTERNAL_RISK_EVENTS")


class DuckDBRepository(BaseRepository):
    """DuckDB repository implementation for local analytics."""

    def __init__(self, connection=None):
        self._conn = connection

    @property
    def conn(self):
        if self._conn is None:
            return DatabaseManager.get_duckdb_connection()
        return self._conn

    def get_table(self, table_name: str) -> pd.DataFrame:
        try:
            return self.conn.execute(f"SELECT * FROM {table_name}").df()
        except Exception as e:
            logger.warning(f"DuckDB: Error reading table '{table_name}': {e}. Returning empty DataFrame.")
            return pd.DataFrame()

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        try:
            if params:
                return self.conn.execute(query, params).df()
            return self.conn.execute(query).df()
        except Exception as e:
            logger.warning(f"DuckDB: Error executing query '{query}': {e}. Returning empty DataFrame.")
            return pd.DataFrame()

    def write_table(self, df: pd.DataFrame, table_name: str, overwrite: bool = False) -> bool:
        try:
            if df.empty:
                logger.info(f"DuckDB: DataFrame for '{table_name}' is empty. Skipping write.")
                return True
            self.conn.register("_temp_df_view", df)
            table_exists = False
            try:
                chk = self.conn.execute(
                    f"SELECT count(*) FROM information_schema.tables WHERE table_name ILIKE '{table_name}'"
                ).fetchone()
                table_exists = (chk is not None and chk[0] > 0)
            except Exception:
                table_exists = False

            if overwrite or not table_exists:
                self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM _temp_df_view")
            else:
                self.conn.execute(f"INSERT INTO {table_name} SELECT * FROM _temp_df_view")
            self.conn.unregister("_temp_df_view")
            return True
        except Exception as e:
            logger.error(f"DuckDB: Error writing to table '{table_name}': {e}")
            return False


class SnowflakeRepository(BaseRepository):
    """Snowflake repository implementation for cloud deployments."""

    def __init__(self, session=None):
        self._session = session

    @property
    def session(self):
        if self._session is None:
            return DatabaseManager.get_snowflake_session()
        return self._session

    def get_table(self, table_name: str) -> pd.DataFrame:
        if self.session is None:
            logger.warning(f"Snowflake: No active session. Returning empty DataFrame for '{table_name}'.")
            return pd.DataFrame()
        try:
            db_schema = f"{settings.SNOWFLAKE_DATABASE}.{settings.SNOWFLAKE_SCHEMA}"
            return self.session.sql(f"SELECT * FROM {db_schema}.{table_name}").to_pandas()
        except Exception as e:
            logger.warning(f"Snowflake: Error reading table '{table_name}': {e}. Returning empty DataFrame.")
            return pd.DataFrame()

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        if self.session is None:
            logger.warning("Snowflake: No active session. Returning empty DataFrame.")
            return pd.DataFrame()
        try:
            return self.session.sql(query, params=params).to_pandas()
        except Exception as e:
            logger.warning(f"Snowflake: Error executing query '{query}': {e}. Returning empty DataFrame.")
            return pd.DataFrame()

    def write_table(self, df: pd.DataFrame, table_name: str, overwrite: bool = False) -> bool:
        if self.session is None:
            logger.warning(f"Snowflake: No active session. Cannot write to '{table_name}'.")
            return False
        try:
            mode = "overwrite" if overwrite else "append"
            self.session.write_pandas(df, table_name, auto_create_table=False, overwrite=(mode == "overwrite"))
            return True
        except Exception as e:
            logger.error(f"Snowflake: Error writing to table '{table_name}': {e}")
            return False


def get_repository() -> BaseRepository:
    """Factory to get repository based on active configuration."""
    backend_type = settings.DATA_BACKEND.lower()
    if backend_type == "snowflake":
        return SnowflakeRepository()
    return DuckDBRepository()
