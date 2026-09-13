"""Database session and connection management for PROVISYN."""
from typing import Optional, Any
import duckdb
from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    _duckdb_conn: Optional[duckdb.DuckDBPyConnection] = None
    _snowflake_session: Optional[Any] = None

    @classmethod
    def get_duckdb_connection(cls) -> duckdb.DuckDBPyConnection:
        """Get or initialize a DuckDB connection."""
        if cls._duckdb_conn is None:
            db_path = settings.DUCKDB_PATH
            logger.info(f"Connecting to DuckDB database at: {db_path}")
            cls._duckdb_conn = duckdb.connect(database=db_path, read_only=False)
        return cls._duckdb_conn

    @classmethod
    def set_duckdb_connection(cls, conn: duckdb.DuckDBPyConnection) -> None:
        """Explicitly set the DuckDB connection (useful for testing e.g. :memory:)."""
        cls._duckdb_conn = conn

    @classmethod
    def get_snowflake_session(cls) -> Optional[Any]:
        """Get Snowflake active session if running within Snowpark/SiS."""
        if cls._snowflake_session is None:
            try:
                from snowflake.snowpark.context import get_active_session
                cls._snowflake_session = get_active_session()
                logger.info("Connected to active Snowflake session.")
            except Exception as e:
                logger.debug(f"Snowflake active session not available: {e}")
                cls._snowflake_session = None
        return cls._snowflake_session

    @classmethod
    def set_snowflake_session(cls, session: Any) -> None:
        """Explicitly set Snowflake session (e.g. for testing/mocking)."""
        cls._snowflake_session = session

    @classmethod
    def close(cls) -> None:
        """Close connections."""
        if cls._duckdb_conn is not None:
            try:
                cls._duckdb_conn.close()
            except Exception:
                pass
            cls._duckdb_conn = None
        cls._snowflake_session = None
