"""
Tests for src/db.py

Covers:
- get_connection returns a DuckDBPyConnection
- execute_ddl creates all five star schema tables
"""
import duckdb
from src.db import get_connection, execute_ddl


def test_get_connection_returns_duckdb_connection():
    # Call get_connection with ':memory:', assert isinstance DuckDBPyConnection
    # TODO: implement


def test_execute_ddl_creates_all_tables(in_memory_db):
    # Query information_schema.tables, assert all five tables exist:
    # fact_loans, dim_borrower, dim_loan_grade, dim_time, dim_purpose
    # TODO: implement
