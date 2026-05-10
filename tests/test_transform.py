"""
Tests for src/transform.py

Covers (11 tests):
- clean_rate_column strips % and casts to decimal float
- parse_issue_date extracts year, month, quarter from 'Jan-2015' format
- parse_term_months extracts integer from ' 36 months'
- build_dim_borrower deduplicates and has correct columns
- build_dim_loan_grade deduplicates and has correct columns
- build_dim_time deduplicates and has correct columns
- build_dim_purpose deduplicates and has correct columns
- build_fact_table sets is_default=True for Charged Off
- build_fact_table sets is_default=False for Fully Paid
- int_rate in fact table is float dtype
- null_rate_report returns 0.0 for clean fixture data
"""
import pandas as pd
import pytest
from src.transform import (
    clean_rate_column,
    parse_issue_date,
    parse_term_months,
    build_dim_borrower,
    build_dim_loan_grade,
    build_dim_time,
    build_dim_purpose,
    build_fact_table,
    null_rate_report,
)


def test_clean_rate_column_strips_percent_and_casts_to_float():
    series = pd.Series(["10.99%", "18.49%"])
    result = clean_rate_column(series)
    assert result.dtype == float
    assert abs(result.iloc[0] - 0.1099) < 1e-6
    assert abs(result.iloc[1] - 0.1849) < 1e-6


def test_clean_rate_column_handles_numeric_percent_points():
    series = pd.Series([10.99, 18.49], dtype="float64")
    result = clean_rate_column(series)
    assert abs(result.iloc[0] - 0.1099) < 1e-6
    assert abs(result.iloc[1] - 0.1849) < 1e-6


def test_clean_rate_column_sub_one_percent_string():
    series = pd.Series(["0.99%"])
    result = clean_rate_column(series)
    assert abs(result.iloc[0] - 0.0099) < 1e-9


def test_parse_issue_date_extracts_year_month_quarter():
    series = pd.Series(["Jan-2015", "Mar-2017"])
    result = parse_issue_date(series)
    assert list(result.columns) == ["year", "month", "quarter"]
    assert result.iloc[0]["year"] == 2015
    assert result.iloc[0]["month"] == 1
    assert result.iloc[0]["quarter"] == 1
    assert result.iloc[1]["year"] == 2017
    assert result.iloc[1]["month"] == 3
    assert result.iloc[1]["quarter"] == 1


def test_parse_term_months_extracts_integer():
    series = pd.Series([" 36 months", " 60 months"])
    result = parse_term_months(series)
    assert result.iloc[0] == 36
    assert result.iloc[1] == 60
    assert result.dtype == int


def test_build_dim_borrower_deduplicates_and_has_correct_columns(sample_raw_df):
    # Add a duplicate of row 0 — dim should collapse it to 2 unique profiles.
    df_with_dup = pd.concat([sample_raw_df, sample_raw_df.iloc[[0]]], ignore_index=True)
    dim = build_dim_borrower(df_with_dup)
    assert set(dim.columns) == {
        "borrower_id", "addr_state", "zip_code",
        "home_ownership", "emp_length", "verification_status",
    }
    assert len(dim) == 2  # duplicate collapsed


def test_build_dim_loan_grade_deduplicates_and_has_correct_columns(sample_raw_df):
    df_with_dup = pd.concat([sample_raw_df, sample_raw_df.iloc[[1]]], ignore_index=True)
    dim = build_dim_loan_grade(df_with_dup)
    assert set(dim.columns) == {"grade_id", "grade", "sub_grade"}
    assert len(dim) == 2


def test_build_dim_time_deduplicates_and_has_correct_columns(sample_raw_df):
    df_with_dup = pd.concat([sample_raw_df, sample_raw_df.iloc[[0]]], ignore_index=True)
    dim = build_dim_time(df_with_dup)
    assert set(dim.columns) == {"time_id", "year", "month", "quarter"}
    assert len(dim) == 2


def test_build_dim_purpose_deduplicates_and_has_correct_columns(sample_raw_df):
    df_with_dup = pd.concat([sample_raw_df, sample_raw_df.iloc[[0]]], ignore_index=True)
    dim = build_dim_purpose(df_with_dup)
    assert set(dim.columns) == {"purpose_id", "purpose", "term"}
    assert len(dim) == 2


def _build_all_dims(df: pd.DataFrame):
    return (
        build_dim_borrower(df),
        build_dim_loan_grade(df),
        build_dim_time(df),
        build_dim_purpose(df),
    )


def test_build_fact_table_is_default_true_for_charged_off(sample_raw_df):
    dims = _build_all_dims(sample_raw_df)
    fact = build_fact_table(sample_raw_df, *dims)
    charged_off = fact[fact["loan_status"] == "Charged Off"]
    assert charged_off["is_default"].all()


def test_build_fact_table_is_default_false_for_fully_paid(sample_raw_df):
    dims = _build_all_dims(sample_raw_df)
    fact = build_fact_table(sample_raw_df, *dims)
    fully_paid = fact[fact["loan_status"] == "Fully Paid"]
    assert (~fully_paid["is_default"]).all()


def test_build_fact_table_int_rate_is_float_dtype(sample_raw_df):
    dims = _build_all_dims(sample_raw_df)
    fact = build_fact_table(sample_raw_df, *dims)
    assert fact["int_rate"].dtype == float


def test_null_rate_report_returns_zero_for_clean_data(sample_raw_df):
    report = null_rate_report(sample_raw_df)
    for col, rate in report.items():
        assert rate == 0.0, f"Expected 0.0 null rate for '{col}', got {rate}"
