"""
DuckDB connection helper.

Provides get_connection() and execute_ddl() used by all other
src/ modules and the pipeline orchestrator.
"""
from pathlib import Path
import duckdb


_DEFAULT_DB_PATH = "warehouse.duckdb"
_DDL_PATH = Path("schema/create_tables.sql")


def get_connection(db_path: str = _DEFAULT_DB_PATH) -> duckdb.DuckDBPyConnection:
    """Return a DuckDB connection to db_path (file or ':memory:')."""
    # TODO: implement


def execute_ddl(
    con: duckdb.DuckDBPyConnection,
    ddl_path: Path = _DDL_PATH,
) -> None:
    """Read DDL file and execute against the given connection."""
    # TODO: implement
