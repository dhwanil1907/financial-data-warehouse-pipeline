"""
Build a small sample warehouse from the full one.

Keeps every Nth loan (by loan_id) and only the dimension rows those loans use,
so the dashboard can run without the 1.6 GB CSV.

  uv run python -m src.make_sample --db warehouse.duckdb --out data/sample.duckdb
"""
from __future__ import annotations

import argparse
from pathlib import Path

from src.db import execute_ddl, get_connection

DEFAULT_EVERY = 40

# (dimension table, key column) pairs referenced by fact_loans.
DIMENSIONS = [
    ("dim_borrower", "borrower_id"),
    ("dim_loan_grade", "grade_id"),
    ("dim_time", "time_id"),
    ("dim_purpose", "purpose_id"),
]


def build_sample(source_db: str, out_path: str, every: int = DEFAULT_EVERY) -> dict[str, int]:
    """Write a sample warehouse to out_path and return its row counts."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)

    keep = f"loan_id % {int(every)} = 0"
    con = get_connection(str(out))
    try:
        execute_ddl(con)
        con.execute(f"ATTACH '{source_db}' AS full_db (READ_ONLY)")
        for table, key in DIMENSIONS:
            con.execute(
                f"""
                INSERT INTO {table}
                SELECT * FROM full_db.{table}
                WHERE {key} IN (SELECT {key} FROM full_db.fact_loans WHERE {keep})
                """
            )
        con.execute(f"INSERT INTO fact_loans SELECT * FROM full_db.fact_loans WHERE {keep}")
        con.execute("DETACH full_db")
        tables = ["fact_loans", *[table for table, _ in DIMENSIONS]]
        return {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}
    finally:
        con.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a sample warehouse from the full one.")
    parser.add_argument("--db", default="warehouse.duckdb", help="full warehouse to sample")
    parser.add_argument("--out", default="data/sample.duckdb", help="sample file to write")
    parser.add_argument("--every", type=int, default=DEFAULT_EVERY, help="keep every Nth loan_id")
    args = parser.parse_args()

    for table, count in build_sample(args.db, args.out, args.every).items():
        print(f"{table}: {count:,}")


if __name__ == "__main__":
    main()
