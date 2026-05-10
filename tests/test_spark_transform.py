"""Tests for src/spark_transform.py (local Spark; first run can take ~15s)."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from pyspark.sql import SparkSession

from src.spark_transform import (
    compute_avg_loan_by_year,
    compute_default_rate_by_grade,
    create_spark_session,
    run_spark_pipeline,
    write_parquet,
)


def _java_runtime_ok() -> bool:
    """True when ``java -version`` succeeds (macOS stub /usr/bin/java fails)."""
    java = shutil.which("java")
    if not java:
        return False
    try:
        proc = subprocess.run(
            [java, "-version"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    err = (proc.stderr or "").lower()
    return proc.returncode == 0 and "version" in err


pytestmark = pytest.mark.skipif(
    not _java_runtime_ok(),
    reason="PySpark needs a working JDK (install JDK 17+; macOS stub java is not enough).",
)


@pytest.fixture
def spark() -> SparkSession:
    session = create_spark_session("financial-dw-test")
    yield session
    session.stop()


@pytest.fixture
def tiny_loans_csv(tmp_path: Path) -> str:
    """Minimal CSV matching Lending Club column names used by Spark layer."""
    p = tmp_path / "tiny.csv"
    p.write_text(
        "id,grade,loan_status,loan_amnt,issue_d\n"
        "1,A,Fully Paid,10000,Jan-2015\n"
        "2,A,Charged Off,20000,Jan-2015\n"
        "3,B,Fully Paid,15000,Mar-2017\n"
    )
    return str(p)


def test_create_spark_session_returns_spark_session(spark: SparkSession) -> None:
    assert isinstance(spark, SparkSession)
    assert spark.sparkContext.master.startswith("local")


def test_compute_default_rate_by_grade_columns_and_bounds(spark, tiny_loans_csv) -> None:
    from src.spark_transform import _read_loans_csv

    df = _read_loans_csv(spark, tiny_loans_csv)
    out = compute_default_rate_by_grade(df)
    cols = set(out.columns)
    assert cols == {"grade", "default_rate"}
    rows = {r["grade"]: r["default_rate"] for r in out.collect()}
    assert 0.0 <= rows["A"] <= 1.0
    assert 0.0 <= rows["B"] <= 1.0
    assert abs(rows["A"] - 0.5) < 1e-9
    assert abs(rows["B"] - 0.0) < 1e-9


def test_compute_avg_loan_by_year_columns(spark, tiny_loans_csv) -> None:
    from src.spark_transform import _read_loans_csv

    df = _read_loans_csv(spark, tiny_loans_csv)
    out = compute_avg_loan_by_year(df)
    assert set(out.columns) == {"issue_year", "avg_loan_amount"}
    rows = {int(r["issue_year"]): r["avg_loan_amount"] for r in out.collect()}
    assert abs(rows[2015] - 15000.0) < 1e-6
    assert abs(rows[2017] - 15000.0) < 1e-6


def test_write_parquet_creates_parquet_files(spark, tiny_loans_csv, tmp_path) -> None:
    from src.spark_transform import _read_loans_csv

    df = _read_loans_csv(spark, tiny_loans_csv)
    out_dir = tmp_path / "pq"
    write_parquet(df, str(out_dir))
    parquet_files = list(out_dir.rglob("*.parquet"))
    assert len(parquet_files) >= 1


def test_run_spark_pipeline_writes_three_trees(tiny_loans_csv, tmp_path) -> None:
    out = tmp_path / "processed"
    run_spark_pipeline(tiny_loans_csv, str(out))
    assert (out / "raw_loans").exists()
    assert (out / "default_rate_by_grade").exists()
    assert (out / "avg_loan_by_year").exists()
    assert any((out / "raw_loans").rglob("*.parquet"))
