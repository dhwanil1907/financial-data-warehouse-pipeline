"""
ETL orchestrator — extract → transform → load into DuckDB.

Run from the project root so `schema/create_tables.sql` resolves:

    uv run python -m src.pipeline --csv data/raw/lending_club_loans.csv --db warehouse.duckdb
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

from src.db import execute_ddl, get_connection
from src.extract import load_raw_csv, validate_schema
from src.load import get_row_counts, load_dimension, load_fact
from src.transform import (
    build_dim_borrower,
    build_dim_loan_grade,
    build_dim_purpose,
    build_dim_time,
    build_fact_table,
    null_rate_report,
)

# Columns checked for null rates before transform (plan § Task 7).
QUALITY_COLUMNS: list[str] = [
    "id",
    "loan_status",
    "grade",
    "loan_amnt",
    "int_rate",
    "addr_state",
    "issue_d",
]

NULL_RATE_WARN_THRESHOLD = 0.05


def _print_quality_report(df, columns: list[str], threshold: float) -> None:
    report = null_rate_report(df)
    print("\n=== Data quality (null rates before transform) ===")
    flagged = False
    for col in columns:
        if col not in df.columns:
            print(f"  {col}: (column missing from DataFrame)")
            flagged = True
            continue
        rate = report[col]
        pct = rate * 100.0
        flag = ""
        if rate > threshold:
            flag = "  ** exceeds {:.0%} nulls **".format(threshold)
            flagged = True
        print(f"  {col}: {pct:.2f}% null{flag}")
    if flagged:
        print("\nWarning: one or more key columns exceed {:.0%} null rate.".format(threshold))
    else:
        print("\nAll listed key columns are at or below {:.0%} null rate.".format(threshold))


def _print_row_counts(counts: dict[str, int]) -> None:
    print("\n=== Final row counts ===")
    for table in sorted(counts.keys()):
        print(f"  {table}: {counts[table]:,}")


def run_pipeline(csv_path: Path, db_path: str) -> dict[str, int]:
    """Load CSV, validate, transform, insert into DuckDB. Returns table row counts.

    Re-runs recreate the schema from DDL (drops existing tables) then load fresh.
    """
    con: duckdb.DuckDBPyConnection
    con = get_connection(db_path)
    try:
        execute_ddl(con)

        raw = load_raw_csv(str(csv_path))
        validate_schema(raw)
        _print_quality_report(raw, QUALITY_COLUMNS, NULL_RATE_WARN_THRESHOLD)

        dim_borrower = build_dim_borrower(raw)
        dim_loan_grade = build_dim_loan_grade(raw)
        dim_time = build_dim_time(raw)
        dim_purpose = build_dim_purpose(raw)
        fact = build_fact_table(
            raw,
            dim_borrower,
            dim_loan_grade,
            dim_time,
            dim_purpose,
        )

        load_dimension(con, dim_borrower, "dim_borrower")
        load_dimension(con, dim_loan_grade, "dim_loan_grade")
        load_dimension(con, dim_time, "dim_time")
        load_dimension(con, dim_purpose, "dim_purpose")
        load_fact(con, fact)

        counts = get_row_counts(con)
        _print_row_counts(counts)
        return counts
    finally:
        con.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lending Club ETL: CSV → star schema in DuckDB.",
    )
    parser.add_argument(
        "--csv",
        required=True,
        type=Path,
        help="Path to accepted_2007_to_2018Q4.csv (or symlink lending_club_loans.csv)",
    )
    parser.add_argument(
        "--db",
        default="warehouse.duckdb",
        help="DuckDB database file path (default: warehouse.duckdb)",
    )
    args = parser.parse_args(argv)

    if not args.csv.is_file():
        print(f"Error: CSV file not found: {args.csv}", file=sys.stderr)
        return 1

    run_pipeline(args.csv, args.db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
