"""
Tests for src/db.py

Covers:
- get_connection returns a DuckDBPyConnection
- execute_ddl creates all five star schema tables
"""
import duckdb
from src.db import get_connection


def test_get_connection_returns_duckdb_connection():
    con = get_connection(":memory:")
    assert isinstance(con, duckdb.DuckDBPyConnection)
    con.close()


def test_execute_ddl_creates_all_tables(in_memory_db):
    expected = {"fact_loans", "dim_borrower", "dim_loan_grade", "dim_time", "dim_purpose"}
    rows = in_memory_db.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()
    actual = {row[0] for row in rows}
    assert expected == actual
