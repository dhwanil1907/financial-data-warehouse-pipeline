"""Integration test for src.pipeline.run_pipeline."""
from pathlib import Path

from src.pipeline import run_pipeline


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
