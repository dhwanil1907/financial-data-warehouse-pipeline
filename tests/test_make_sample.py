"""Tests for src/make_sample.py."""
from __future__ import annotations

from src.db import execute_ddl, get_connection
from src.make_sample import build_sample


def _build_source(path: str) -> None:
    con = get_connection(path)
    execute_ddl(con)
    con.execute("INSERT INTO dim_borrower VALUES (1, 'CA', '90001', 'RENT', '2 years', 'Verified')")
    con.execute("INSERT INTO dim_borrower VALUES (2, 'NY', '10001', 'OWN', '5 years', 'Verified')")
    con.execute("INSERT INTO dim_loan_grade VALUES (1, 'A', 'A1'), (2, 'B', 'B1')")
    con.execute("INSERT INTO dim_time VALUES (1, 2015, 1, 1)")
    con.execute("INSERT INTO dim_purpose VALUES (1, 'credit_card', '36 months')")
    # loan_id 40 is kept (40 % 40 = 0); loan_id 41 is not and is the only user of borrower 2.
    for loan_id, borrower_id, grade_id in [(40, 1, 1), (41, 2, 2)]:
        con.execute(
            "INSERT INTO fact_loans VALUES (?, ?, ?, 1, 1, 1000, 1000, 0.1, 30, 50000, 10,"
            " 1100, 1000, 100, 0, FALSE, 'Fully Paid')",
            [loan_id, borrower_id, grade_id],
        )
    con.close()


def test_keeps_every_nth_loan_and_only_used_dimension_rows(tmp_path):
    source = str(tmp_path / "full.duckdb")
    out = str(tmp_path / "out" / "sample.duckdb")
    _build_source(source)

    counts = build_sample(source, out, every=40)

    assert counts == {
        "fact_loans": 1,
        "dim_borrower": 1,
        "dim_loan_grade": 1,
        "dim_time": 1,
        "dim_purpose": 1,
    }


def test_rebuilding_replaces_the_existing_sample(tmp_path):
    source = str(tmp_path / "full.duckdb")
    out = str(tmp_path / "sample.duckdb")
    _build_source(source)

    build_sample(source, out, every=40)
    counts = build_sample(source, out, every=40)

    assert counts["fact_loans"] == 1
