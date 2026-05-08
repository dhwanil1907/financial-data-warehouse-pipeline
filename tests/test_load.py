"""
Tests for src/load.py

Covers:
- load_dimension inserts rows into a dimension table
- load_dimension is idempotent (no duplicates on a second run)
- load_fact inserts rows into fact_loans
- get_row_counts returns a dict containing all five table names
"""
import pytest
from src.load import load_dimension, load_fact, get_row_counts
from src.transform import (
    build_dim_borrower,
    build_dim_loan_grade,
    build_dim_time,
    build_dim_purpose,
    build_fact_table,
)


@pytest.fixture
def dims(sample_raw_df):
    return {
        "dim_borrower":   build_dim_borrower(sample_raw_df),
        "dim_loan_grade": build_dim_loan_grade(sample_raw_df),
        "dim_time":       build_dim_time(sample_raw_df),
        "dim_purpose":    build_dim_purpose(sample_raw_df),
    }


@pytest.fixture
def fact(sample_raw_df, dims):
    return build_fact_table(
        sample_raw_df,
        dims["dim_borrower"],
        dims["dim_loan_grade"],
        dims["dim_time"],
        dims["dim_purpose"],
    )


def test_load_dimension_inserts_rows(in_memory_db, dims):
    load_dimension(in_memory_db, dims["dim_borrower"], "dim_borrower")
    count = in_memory_db.execute("SELECT COUNT(*) FROM dim_borrower").fetchone()[0]
    assert count == len(dims["dim_borrower"])


def test_load_dimension_is_idempotent(in_memory_db, dims):
    load_dimension(in_memory_db, dims["dim_borrower"], "dim_borrower")
    load_dimension(in_memory_db, dims["dim_borrower"], "dim_borrower")
    count = in_memory_db.execute("SELECT COUNT(*) FROM dim_borrower").fetchone()[0]
    assert count == len(dims["dim_borrower"])  # no duplicates


def test_load_fact_inserts_rows(in_memory_db, dims, fact):
    for table_name, df in dims.items():
        load_dimension(in_memory_db, df, table_name)
    load_fact(in_memory_db, fact)
    count = in_memory_db.execute("SELECT COUNT(*) FROM fact_loans").fetchone()[0]
    assert count == len(fact)


def test_get_row_counts_returns_dict_with_all_tables(in_memory_db, dims, fact):
    for table_name, df in dims.items():
        load_dimension(in_memory_db, df, table_name)
    load_fact(in_memory_db, fact)
    counts = get_row_counts(in_memory_db)
    expected_tables = {"dim_borrower", "dim_loan_grade", "dim_time", "dim_purpose", "fact_loans"}
    assert expected_tables == set(counts.keys())
    assert all(isinstance(v, int) for v in counts.values())
