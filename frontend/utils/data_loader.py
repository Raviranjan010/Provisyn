"""Parallel query execution and data loading utilities for PROVISYN."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import logging
import time
from typing import Dict, Any, Optional
from backend.data.repository import get_repository, BaseRepository

DB_SCHEMA = "SUPPLY_CHAIN_RISK.SUPPLY_CHAIN_RISK"
logger = logging.getLogger(__name__)

def get_data_repository() -> BaseRepository:
    """Get configured repository."""
    return get_repository()

def run_queries_parallel(
    session,
    queries: Dict[str, str],
    max_workers: int = 4,
    return_empty_on_error: bool = True
) -> Dict[str, pd.DataFrame]:
    """Execute multiple independent SQL queries in parallel using ThreadPoolExecutor."""
    if not queries:
        return {}
    
    start_time = time.time()
    results: Dict[str, pd.DataFrame] = {}
    repo = get_data_repository()
    
    def execute_query(name: str, query: str) -> tuple:
        query_start = time.time()
        try:
            if session is not None and hasattr(session, "sql"):
                df = session.sql(query).to_pandas()
            else:
                df = repo.execute_query(query)
            elapsed = time.time() - query_start
            logger.debug(f"Query '{name}' completed in {elapsed:.2f}s: {len(df)} rows")
            return name, df
        except Exception as e:
            elapsed = time.time() - query_start
            logger.error(f"Query '{name}' failed after {elapsed:.2f}s: {e}")
            if return_empty_on_error:
                return name, pd.DataFrame()
            else:
                raise

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_name = {
            executor.submit(execute_query, name, query): name
            for name, query in queries.items()
        }
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                query_name, result_df = future.result()
                results[query_name] = result_df
            except Exception as e:
                logger.error(f"Failed to get result for '{name}': {e}")
                if return_empty_on_error:
                    results[name] = pd.DataFrame()
                else:
                    raise
    
    total_elapsed = time.time() - start_time
    logger.debug(f"Parallel query execution completed in {total_elapsed:.2f}s for {len(queries)} queries")
    return results

def run_query_safe(session, query: str, default_value: Any = None) -> Any:
    """Execute a single query with fallback on error."""
    try:
        if session is not None and hasattr(session, "sql"):
            return session.sql(query).to_pandas()
        return get_data_repository().execute_query(query)
    except Exception as e:
        logger.warning(f"Query failed, returning default: {e}")
        return default_value
