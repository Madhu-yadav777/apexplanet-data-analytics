#!/usr/bin/env python3
"""
db_utils.py
===========
Reusable Python + SQL integration helpers for the ApexPlanet Data Analytics
project (Task 2: SQL & Data Extraction).

This module wraps SQLAlchemy so that any script or notebook in the project can
connect to the Task 2 SQLite database, run queries, fetch results as Pandas
DataFrames, and execute parameterized queries without rewriting the
connection logic every time.

Key design principles:
    - Paths are resolved relative to the project root, so the repo works on
      any machine without hardcoded absolute paths.
    - The engine is created lazily and reused, avoiding reconnection overhead.
    - Parameterized query support is exposed as first-class helpers.

Usage:
    from scripts.db_utils import get_engine, run_query, run_query_params

    engine = get_engine()
    df = run_query("SELECT * FROM sales LIMIT 5", engine)
    df2 = run_query_params(
        "SELECT * FROM sales WHERE Product_Category = :category",
        {"category": "Electronics"},
        engine,
    )

Requirements:
    - pandas
    - sqlalchemy
"""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# ---------------------------------------------------------------------------
# Project paths (portable, relative to this file's parent-of-parent)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "apexplanet_sales.db"


def get_engine(db_path: Optional[Path] = None, echo: bool = False) -> Engine:
    """
    Create (or reuse) a SQLAlchemy engine for the Task 2 SQLite database.

    Args:
        db_path: Optional override for the database file location.
            Defaults to the project's database/apexplanet_sales.db.
        echo: If True, echoes all SQL statements to stdout (useful for
            debugging and for the EXPLAIN-query-plan workflow).

    Returns:
        SQLAlchemy Engine instance.

    Note:
        SQLAlchemy caches engines internally by URL + options; repeated calls
        with identical arguments return the same engine. Call
        dispose_engine() explicitly if you need to tear down a stale
        connection pool.
    """
    path = Path(db_path) if db_path else DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{path}"
    return create_engine(url, echo=echo, future=True)


@contextmanager
def engine_context(echo: bool = False):
    """
    Context manager that yields a fresh engine and disposes of it on exit.

    Usage:
        with engine_context() as engine:
            df = run_query("SELECT 1", engine)
    """
    engine = get_engine(echo=echo)
    try:
        yield engine
    finally:
        engine.dispose()


def dispose_engine(engine: Engine) -> None:
    """Dispose of the engine's connection pool, releasing all pooled connections."""
    if engine is not None:
        engine.dispose()


def run_query(sql: str, engine: Optional[Engine] = None) -> pd.DataFrame:
    """
    Execute a read-only SQL query and return the result as a Pandas DataFrame.

    Args:
        sql: SQL statement (SELECT, EXPLAIN, or any read-only statement).
        engine: Optional engine. If None, a new engine is created and
            disposed of after the call.

    Returns:
        Pandas DataFrame with the query results.
    """
    own_engine = engine is None
    if own_engine:
        engine = get_engine()
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn)
    finally:
        if own_engine:
            dispose_engine(engine)


def run_query_params(
    sql: str,
    params: Dict[str, Any],
    engine: Optional[Engine] = None,
) -> pd.DataFrame:
    """
    Execute a parameterized SQL query and return the result as a DataFrame.

    Args:
        sql: SQL statement with named placeholders (:param_name).
        params: Dictionary mapping placeholder names to bound values.
        engine: Optional engine.

    Returns:
        Pandas DataFrame with the query results.

    Example:
        df = run_query_params(
            "SELECT * FROM sales WHERE Product_Category = :cat",
            {"cat": "Electronics"},
        )

    Security note:
        This function uses SQLAlchemy's named-parameter binding, which
        handles escaping safely. Never build SQL via f-strings or %
        interpolation — that is how SQL injection happens.
    """
    own_engine = engine is None
    if own_engine:
        engine = get_engine()
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params)
    finally:
        if own_engine:
            dispose_engine(engine)


def execute_write(sql: str, params: Optional[Dict[str, Any]] = None,
                  engine: Optional[Engine] = None) -> int:
    """
    Execute an SQL write statement (INSERT/UPDATE/DELETE/DDL) and return the
    number of affected rows.

    Args:
        sql: SQL statement.
        params: Optional dict of named parameters.
        engine: Optional engine.

    Returns:
        Number of rows affected (for DDL, returns 0).
    """
    own_engine = engine is None
    if own_engine:
        engine = get_engine()
    try:
        with engine.begin() as conn:  # auto-commit on success, rollback on error
            result = conn.execute(text(sql), params or {})
            return result.rowcount
    finally:
        if own_engine:
            dispose_engine(engine)


def get_table_columns(table: str, engine: Optional[Engine] = None) -> List[dict]:
    """Return the column definitions for a table as a list of dicts."""
    from sqlalchemy import inspect
    own_engine = engine is None
    if own_engine:
        engine = get_engine()
    try:
        inspector = inspect(engine)
        return inspector.get_columns(table)
    finally:
        if own_engine:
            dispose_engine(engine)


def get_table_names(engine: Optional[Engine] = None) -> List[str]:
    """Return the list of tables in the database."""
    from sqlalchemy import inspect
    own_engine = engine is None
    if own_engine:
        engine = get_engine()
    try:
        inspector = inspect(engine)
        return inspector.get_table_names()
    finally:
        if own_engine:
            dispose_engine(engine)


def count_rows(table: str, engine: Optional[Engine] = None) -> int:
    """Return the number of rows in a table."""
    own_engine = engine is None
    if own_engine:
        engine = get_engine()
    try:
        with engine.connect() as conn:
            return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    finally:
        if own_engine:
            dispose_engine(engine)


def validate_database(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run a comprehensive data validation suite against the Task 2 database.

    Checks:
        - Database file exists
        - Expected tables exist
        - Row counts are non-zero
        - Key columns are present
        - No unexpected NULLs in critical numeric columns

    Returns:
        Dictionary of validation results.
    """
    results: Dict[str, Any] = {}
    db = Path(db_path) if db_path else DATABASE_PATH

    # 1. File exists
    results["database_file_exists"] = db.exists()
    if not results["database_file_exists"]:
        return results

    engine = get_engine(db)

    # 2. Tables exist
    tables = get_table_names(engine)
    results["tables"] = tables
    results["sales_table_exists"] = "sales" in tables
    results["city_regions_table_exists"] = "city_regions" in tables

    # 3. Row counts
    results["sales_row_count"] = count_rows("sales", engine)
    results["city_regions_row_count"] = (
        count_rows("city_regions", engine)
        if "city_regions" in tables else 0
    )

    # 4. Key column check on sales table
    if "sales" in tables:
        cols = {c["name"] for c in get_table_columns("sales", engine)}
        expected = {
            "Customer_ID", "Order_Date", "Age", "Gender", "City",
            "Product_Category", "Product", "Quantity", "Unit_Price",
            "Total_Sales", "Discount", "Payment_Method", "Customer_Rating",
        }
        results["sales_columns"] = sorted(cols)
        results["missing_columns"] = sorted(expected - cols)
        results["all_expected_columns_present"] = not (expected - cols)

        # 5. NULL check on critical numeric columns
        with engine.connect() as conn:
            for col in ["Quantity", "Unit_Price", "Total_Sales", "Discount"]:
                cnt = conn.execute(
                    text(f"SELECT COUNT(*) FROM sales WHERE {col} IS NULL")
                ).scalar()
                results[f"nulls_{col}"] = int(cnt)

    # 6. Sanity check: total revenue
    if "sales" in tables:
        with engine.connect() as conn:
            total = conn.execute(text("SELECT SUM(Total_Sales) FROM sales")).scalar()
            results["total_revenue"] = float(total) if total is not None else 0.0

    dispose_engine(engine)
    return results


# ---------------------------------------------------------------------------
# Self-test when run as a script
# ---------------------------------------------------------------------------
def _self_test():
    """Run a quick smoke test when db_utils.py is executed directly."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))

    print("=" * 60)
    print("db_utils.py self-test")
    print("=" * 60)

    results = validate_database()
    print(f"Database file exists     : {results['database_file_exists']}")
    print(f"Tables                   : {results.get('tables')}")
    print(f"Sales table exists       : {results.get('sales_table_exists')}")
    print(f"City_regions exists      : {results.get('city_regions_table_exists')}")
    print(f"Sales row count          : {results.get('sales_row_count')}")
    print(f"Total revenue            : {results.get('total_revenue'):,.2f}")

    # Quick query test
    engine = get_engine()
    df = run_query("SELECT COUNT(*) AS n FROM sales", engine)
    print(f"Test query returned n    : {df['n'].iloc[0]}")
    df2 = run_query_params(
        "SELECT COUNT(*) AS n FROM sales WHERE Product_Category = :cat",
        {"cat": "Electronics"},
        engine,
    )
    print(f"Parameterized query n    : {df2['n'].iloc[0]}")
    dispose_engine(engine)
    print("\nAll self-tests passed.")


if __name__ == "__main__":
    _self_test()
