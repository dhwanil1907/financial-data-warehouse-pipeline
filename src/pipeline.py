"""
ETL orchestrator — extract → transform → load into DuckDB.

Run from the project root:

    uv run python -m src.pipeline --csv data/raw/lending_club_loans.csv --db warehouse.duckdb
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import duckdb
import pandas as pd

from src.db import execute_ddl, get_connection
from src.extract import load_raw_csv, validate_schema
from src.load import get_row_counts, load_dimension, load_fact
from src.transform import (
    DataQualityError,
    build_dim_borrower,
    build_dim_loan_grade,
    build_dim_purpose,
    build_dim_time,
    build_fact_table,
    filter_valid_loan_rows,
    null_rate_report,
    validate_fact_table,
)

logger = logging.getLogger(__name__)

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


def _log_quality_report(df: pd.DataFrame, columns: list[str], threshold: float) -> None:
    present = [col for col in columns if col in df.columns]
    report = null_rate_report(df, present)
    logger.info("Data quality (null rates before transform)")
    flagged = False
    for col in columns:
        if col not in df.columns:
            logger.warning("  %s: column missing from DataFrame", col)
            flagged = True
            continue
        pct = report[col] * 100.0
        if report[col] > threshold:
            logger.warning("  %s: %.2f%% null  ** exceeds %.0f%% nulls **", col, pct, threshold * 100)
            flagged = True
        else:
            logger.info("  %s: %.2f%% null", col, pct)
    if flagged:
        logger.warning("One or more key columns exceed %.0f%% null rate.", threshold * 100)
    else:
        logger.info("All listed key columns are at or below %.0f%% null rate.", threshold * 100)


def _log_row_counts(counts: dict[str, int]) -> None:
    logger.info("Final row counts")
    for table in sorted(counts.keys()):
        logger.info("  %s: %s", table, f"{counts[table]:,}")


def _verify_loaded_counts(counts: dict[str, int], expected: dict[str, int]) -> None:
    """Raise if a table holds a different row count than was transformed.

    INSERT OR IGNORE skips rows that violate a key without raising, so a
    mismatch here means rows were silently dropped during the load.
    """
    mismatched = {
        table: {"expected": expected[table], "loaded": counts[table]}
        for table in expected
        if counts[table] != expected[table]
    }
    if mismatched:
        raise DataQualityError(f"Loaded row counts differ from transformed rows: {mismatched}")


def run_pipeline(csv_path: Path, db_path: str) -> dict[str, int]:
    """Load CSV, validate, transform, insert into DuckDB. Returns table row counts.

    The CSV is extracted and transformed before the database is opened. The
    schema is then recreated and loaded inside a single transaction, so a
    failure at any point rolls back and leaves the previous warehouse intact.
    """
    raw = load_raw_csv(str(csv_path))
    validate_schema(raw)
    n_raw = len(raw)
    raw = filter_valid_loan_rows(raw)
    if len(raw) < n_raw:
        logger.info(
            "Dropped %d row(s) with non-numeric loan id (CSV footer/summary lines).",
            n_raw - len(raw),
        )

    _log_quality_report(raw, QUALITY_COLUMNS, NULL_RATE_WARN_THRESHOLD)

    dim_borrower = build_dim_borrower(raw)
    dim_loan_grade = build_dim_loan_grade(raw)
    dim_time = build_dim_time(raw)
    dim_purpose = build_dim_purpose(raw)
    fact = build_fact_table(raw, dim_borrower, dim_loan_grade, dim_time, dim_purpose)
    validate_fact_table(fact)

    expected_counts = {
        "dim_borrower": len(dim_borrower),
        "dim_loan_grade": len(dim_loan_grade),
        "dim_time": len(dim_time),
        "dim_purpose": len(dim_purpose),
        "fact_loans": len(fact),
    }

    con: duckdb.DuckDBPyConnection = get_connection(db_path)
    try:
        con.begin()
        try:
            execute_ddl(con)
            load_dimension(con, dim_borrower, "dim_borrower")
            load_dimension(con, dim_loan_grade, "dim_loan_grade")
            load_dimension(con, dim_time, "dim_time")
            load_dimension(con, dim_purpose, "dim_purpose")
            load_fact(con, fact)

            counts = get_row_counts(con)
            _verify_loaded_counts(counts, expected_counts)
            con.commit()
        except Exception:
            con.rollback()
            raise
    finally:
        con.close()

    _log_row_counts(counts)
    return counts


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

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if not args.csv.is_file():
        print(f"Error: CSV file not found: {args.csv}", file=sys.stderr)
        return 1

    try:
        run_pipeline(args.csv, args.db)
    except ValueError as err:
        logger.error("Pipeline failed, warehouse left unchanged: %s", err)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
