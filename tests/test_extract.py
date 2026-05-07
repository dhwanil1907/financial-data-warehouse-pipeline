"""
Tests for src/extract.py

Covers:
- load_raw_csv returns a DataFrame with the correct row count
- validate_schema passes on valid data
- validate_schema raises ValueError on missing columns
- validate_schema raises ValueError on empty DataFrame
- REQUIRED_COLUMNS contains the four sentinel columns
"""
import pytest
import pandas as pd
from src.extract import REQUIRED_COLUMNS, load_raw_csv, validate_schema


def test_required_columns_contains_sentinels():
    for col in ("id", "loan_status", "grade", "loan_amnt"):
        assert col in REQUIRED_COLUMNS


def test_load_raw_csv_returns_dataframe(tmp_path, sample_raw_df):
    csv_file = tmp_path / "loans.csv"
    sample_raw_df.to_csv(csv_file, index=False)
    df = load_raw_csv(str(csv_file))
    assert isinstance(df, pd.DataFrame)
    assert len(df) == len(sample_raw_df)


def test_validate_schema_passes_on_valid_data(sample_raw_df):
    # Should not raise
    validate_schema(sample_raw_df)


def test_validate_schema_raises_on_missing_column(sample_raw_df):
    df = sample_raw_df.drop(columns=["grade"])
    with pytest.raises(ValueError, match="grade"):
        validate_schema(df)


def test_validate_schema_raises_on_empty_dataframe(sample_raw_df):
    empty = sample_raw_df.iloc[0:0]
    with pytest.raises(ValueError, match="empty"):
        validate_schema(empty)


def test_load_raw_csv_row_count(tmp_path, sample_raw_df):
    csv_file = tmp_path / "loans.csv"
    sample_raw_df.to_csv(csv_file, index=False)
    df = load_raw_csv(str(csv_file))
    assert len(df) == 2
