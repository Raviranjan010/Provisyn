"""Unit tests for the repository interface (Phase 2)."""
import duckdb
import pandas as pd
from unittest.mock import MagicMock
from backend.data.repository import DuckDBRepository, SnowflakeRepository

def test_duckdb_repository_missing_table_returns_empty_dataframe():
    """Verify DuckDB repository returns an empty DataFrame instead of raising on a missing table."""
    conn = duckdb.connect(":memory:")
    repo = DuckDBRepository(connection=conn)
    
    # Missing table query
    result = repo.get_table("NON_EXISTENT_TABLE")
    assert isinstance(result, pd.DataFrame)
    assert result.empty

def test_snowflake_repository_missing_table_returns_empty_dataframe():
    """Verify Snowflake repository returns an empty DataFrame instead of raising on a missing table."""
    mock_session = MagicMock()
    mock_session.sql.side_effect = Exception("Table 'NON_EXISTENT_TABLE' does not exist or not authorized")
    repo = SnowflakeRepository(session=mock_session)
    
    result = repo.get_table("NON_EXISTENT_TABLE")
    assert isinstance(result, pd.DataFrame)
    assert result.empty

def test_snowflake_repository_without_session_returns_empty_dataframe():
    """Verify Snowflake repository gracefully handles absence of active session."""
    repo = SnowflakeRepository(session=None)
    result = repo.get_table("VENDORS")
    assert isinstance(result, pd.DataFrame)
    assert result.empty
