"""Integration tests for src.pipeline."""
from pathlib import Path

import duckdb
import pytest

from src import pipeline
from src.pipeline import main, run_pipeline
from src.transform import DataQualityError


def test_run_pipeline_loads_sample_csv(tmp_path: Path, sample_raw_df) -> None:
    csv_path = tmp_path / "loans.csv"
    sample_raw_df.to_csv(csv_path, index=False)
    db_path = str(tmp_path / "pipeline_test.duckdb")
    counts = run_pipeline(csv_path, db_path)
    assert counts["dim_borrower"] == 2
    assert counts["dim_loan_grade"] == 2
    assert counts["dim_time"] == 2
    assert counts["dim_purpose"] == 2
    assert counts["fact_loans"] == len(sample_raw_df)


def test_failed_load_rolls_back_and_keeps_previous_warehouse(
    tmp_path: Path, sample_raw_df, monkeypatch
) -> None:
    csv_path = tmp_path / "loans.csv"
    sample_raw_df.to_csv(csv_path, index=False)
    db_path = str(tmp_path / "pipeline_test.duckdb")
    run_pipeline(csv_path, db_path)

    def fail_fact_load(con, df):
        raise RuntimeError("simulated failure while loading fact_loans")

    monkeypatch.setattr(pipeline, "load_fact", fail_fact_load)
    with pytest.raises(RuntimeError, match="simulated failure"):
        run_pipeline(csv_path, db_path)

    con = duckdb.connect(db_path, read_only=True)
    try:
        assert con.execute("SELECT COUNT(*) FROM fact_loans").fetchone()[0] == len(sample_raw_df)
        assert con.execute("SELECT COUNT(*) FROM dim_borrower").fetchone()[0] == 2
    finally:
        con.close()


def test_run_pipeline_raises_when_loan_ids_repeat(tmp_path: Path, sample_raw_df) -> None:
    repeated = sample_raw_df.copy()
    repeated["id"] = ["10001", "10001"]
    csv_path = tmp_path / "loans.csv"
    repeated.to_csv(csv_path, index=False)
    db_path = tmp_path / "pipeline_test.duckdb"
    with pytest.raises(DataQualityError, match="repeated loan_id"):
        run_pipeline(csv_path, str(db_path))
    assert not db_path.exists()


def test_main_returns_1_when_a_required_column_is_missing(tmp_path: Path, sample_raw_df) -> None:
    csv_path = tmp_path / "loans.csv"
    sample_raw_df.drop(columns=["grade"]).to_csv(csv_path, index=False)
    exit_code = main(["--csv", str(csv_path), "--db", str(tmp_path / "pipeline_test.duckdb")])
    assert exit_code == 1
