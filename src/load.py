"""
Load layer — inserts transformed DataFrames into the DuckDB star schema.

Public API:
    load_dimension(con, df, table_name)   INSERT OR IGNORE into a dimension table
    load_fact(con, df)                    INSERT OR IGNORE into fact_loans
    get_row_counts(con)                   {table_name: row_count} for all five tables
"""
import pandas as pd
import duckdb

_TABLES = ["dim_borrower", "dim_loan_grade", "dim_time", "dim_purpose", "fact_loans"]


def _insert_or_ignore(con: duckdb.DuckDBPyConnection, df: pd.DataFrame, table_name: str) -> None:
    """Register df as a temporary view and INSERT OR IGNORE into table_name."""
    con.register("_load_tmp", df)
    try:
        con.execute(f"INSERT OR IGNORE INTO {table_name} SELECT * FROM _load_tmp")
    finally:
        con.unregister("_load_tmp")


def load_dimension(
    con: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
    table_name: str,
) -> None:
    """Insert dimension rows, silently skipping any that violate the primary key.

    Safe to call multiple times — duplicate rows are ignored rather than
    raising an error, making the load step idempotent.
    """
    _insert_or_ignore(con, df, table_name)


def load_fact(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
    """Insert fact_loans rows, silently skipping duplicates on loan_id."""
    _insert_or_ignore(con, df, "fact_loans")


def get_row_counts(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Return the current row count for each of the five star schema tables."""
    return {
        table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in _TABLES
    }
