"""
Shared pytest fixtures used across all test modules.

Fixtures:
- in_memory_db: fresh DuckDB in-memory connection with star schema applied
- sample_raw_df: minimal DataFrame matching lending_club_loans.csv columns
"""
import pytest
import duckdb
import pandas as pd
from pathlib import Path


@pytest.fixture
def in_memory_db():
    """Fresh in-memory DuckDB connection with star schema for each test."""
    from src.db import get_connection, execute_ddl
    con = get_connection(":memory:")
    execute_ddl(con, Path("schema/create_tables.sql"))
    yield con
    con.close()


@pytest.fixture
def sample_raw_df():
    """Minimal two-row DataFrame matching lending_club_loans.csv columns.

    Row 0: Fully Paid  → is_default = False
    Row 1: Charged Off → is_default = True
    """
    return pd.DataFrame({
        "id":                  ["10001", "10002"],
        "addr_state":          ["IL", "TX"],
        "zip_code":            ["606xx", "752xx"],
        "home_ownership":      ["RENT", "MORTGAGE"],
        "emp_length":          ["5 years", "10+ years"],
        "verification_status": ["Verified", "Not Verified"],
        "annual_inc":          [65000.0, 90000.0],
        "issue_d":             ["Jan-2015", "Mar-2017"],
        "loan_status":         ["Fully Paid", "Charged Off"],
        "loan_amnt":           [15000.0, 25000.0],
        "funded_amnt":         [15000.0, 25000.0],
        "int_rate":            ["10.99%", "18.49%"],
        "installment":         [326.18, 637.58],
        "grade":               ["B", "D"],
        "sub_grade":           ["B3", "D2"],
        "purpose":             ["debt_consolidation", "credit_card"],
        "term":                [" 36 months", " 60 months"],
        "dti":                 [18.5, 29.3],
        "total_pymnt":         [16200.0, 14800.0],
        "total_rec_prncp":     [15000.0, 12500.0],
        "total_rec_int":       [1200.0, 2300.0],
        "recoveries":          [0.0, 4500.0],
    })
