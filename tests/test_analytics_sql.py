"""Smoke-test: every analytics SQL file runs on an empty star schema."""
from pathlib import Path

from src.db import execute_ddl, get_connection


def test_analytics_sql_files_execute_on_empty_schema() -> None:
    con = get_connection(":memory:")
    execute_ddl(con, Path("schema/create_tables.sql"))
    for path in sorted(Path("sql/analytics").glob("*.sql")):
        con.execute(path.read_text())
    con.close()
