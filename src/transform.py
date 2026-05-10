"""
Transform layer — cleans raw Lending Club data and builds star schema DataFrames.

Public API:
    clean_rate_column(series)         strip % and convert to decimal float
    parse_issue_date(series)          'Jan-2015' → DataFrame[year, month, quarter]
    parse_term_months(series)         ' 36 months' → int Series
    build_dim_borrower(df)            borrower dimension DataFrame
    build_dim_loan_grade(df)          loan grade dimension DataFrame
    build_dim_time(df)                time dimension DataFrame
    build_dim_purpose(df)             purpose dimension DataFrame
    build_fact_table(df, *dims)       fact_loans DataFrame with FK surrogates
    null_rate_report(df)              {column: null_fraction} for every column
    row_count_assertion(df, min_rows) raise AssertionError if row count too low
"""
import pandas as pd


# ---------------------------------------------------------------------------
# Column cleaners
# ---------------------------------------------------------------------------

def clean_rate_column(series: pd.Series) -> pd.Series:
    """Normalize int_rate to a decimal float (e.g. 12.99% or 12.99 → 0.1299).

    If the column is numeric (pandas inferred floats from CSV), values greater
    than 1 are treated as percent points (10.99 → 0.1099); values in (0, 1] are
    kept as decimals. Object/string columns strip ``%`` and divide by 100.
    """
    if pd.api.types.is_numeric_dtype(series):
        out = pd.to_numeric(series, errors="coerce").astype(float)
        over_one = out.notna() & (out > 1.0)
        out = out.copy()
        out.loc[over_one] = out.loc[over_one] / 100.0
        return out
    stripped = (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.strip()
    )
    return pd.to_numeric(stripped, errors="coerce").astype(float) / 100.0


def parse_issue_date(series: pd.Series) -> pd.DataFrame:
    """Parse 'Jan-2015' strings into a DataFrame with year, month, quarter columns."""
    parsed = pd.to_datetime(series, format="%b-%Y")
    return pd.DataFrame({
        "year":    parsed.dt.year,
        "month":   parsed.dt.month,
        "quarter": parsed.dt.quarter,
    })


def parse_term_months(series: pd.Series) -> pd.Series:
    """Extract the integer month count from a term string like ' 36 months'."""
    return series.str.strip().str.extract(r"(\d+)")[0].astype(int)


# ---------------------------------------------------------------------------
# Dimension builders
# ---------------------------------------------------------------------------

def build_dim_borrower(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate on borrower natural key and assign a surrogate borrower_id."""
    natural_key = ["addr_state", "zip_code", "home_ownership", "emp_length", "verification_status"]
    dim = (
        df[natural_key]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim.insert(0, "borrower_id", range(1, len(dim) + 1))
    return dim


def build_dim_loan_grade(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate on (grade, sub_grade) and assign a surrogate grade_id."""
    dim = (
        df[["grade", "sub_grade"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim.insert(0, "grade_id", range(1, len(dim) + 1))
    return dim


def build_dim_time(df: pd.DataFrame) -> pd.DataFrame:
    """Parse issue_d, deduplicate on (year, month), and assign a surrogate time_id."""
    time_parts = parse_issue_date(df["issue_d"])
    dim = (
        time_parts
        .drop_duplicates(subset=["year", "month"])
        .reset_index(drop=True)
    )
    dim.insert(0, "time_id", range(1, len(dim) + 1))
    return dim[["time_id", "year", "month", "quarter"]]


def build_dim_purpose(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate on (purpose, term) and assign a surrogate purpose_id.

    Leading/trailing whitespace is stripped from the raw term string
    (e.g. ' 36 months' → '36 months').
    """
    purpose_df = df[["purpose"]].copy()
    purpose_df["term"] = df["term"].str.strip()
    dim = (
        purpose_df
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim.insert(0, "purpose_id", range(1, len(dim) + 1))
    return dim


# ---------------------------------------------------------------------------
# Fact builder
# ---------------------------------------------------------------------------

def build_fact_table(
    df: pd.DataFrame,
    dim_borrower: pd.DataFrame,
    dim_loan_grade: pd.DataFrame,
    dim_time: pd.DataFrame,
    dim_purpose: pd.DataFrame,
) -> pd.DataFrame:
    """Join dimension surrogates into a fact_loans DataFrame.

    Transformations applied:
    - int_rate: % stripped, stored as decimal float
    - is_default: True when loan_status == 'Charged Off'
    - loan_id: raw 'id' column cast to int
    """
    fact = df.copy()

    fact["int_rate"] = clean_rate_column(fact["int_rate"])
    fact["is_default"] = fact["loan_status"] == "Charged Off"
    fact["loan_id"] = fact["id"].astype(int)

    # Derive year/month for time join
    time_parts = parse_issue_date(fact["issue_d"])
    fact["_year"] = time_parts["year"]
    fact["_month"] = time_parts["month"]

    # Strip term for purpose join
    fact["_term"] = fact["term"].str.strip()

    # Join borrower
    fact = fact.merge(
        dim_borrower[["borrower_id", "addr_state", "zip_code",
                      "home_ownership", "emp_length", "verification_status"]],
        on=["addr_state", "zip_code", "home_ownership", "emp_length", "verification_status"],
        how="left",
    )

    # Join grade
    fact = fact.merge(
        dim_loan_grade[["grade_id", "grade", "sub_grade"]],
        on=["grade", "sub_grade"],
        how="left",
    )

    # Join time — rename dim columns to match the _year/_month keys
    dim_time_join = dim_time[["time_id", "year", "month"]].rename(
        columns={"year": "_year", "month": "_month"}
    )
    fact = fact.merge(dim_time_join, on=["_year", "_month"], how="left")

    # Join purpose — rename dim term to match _term key
    dim_purpose_join = dim_purpose[["purpose_id", "purpose", "term"]].rename(
        columns={"term": "_term"}
    )
    fact = fact.merge(dim_purpose_join, on=["purpose", "_term"], how="left")

    fact_cols = [
        "loan_id", "borrower_id", "grade_id", "time_id", "purpose_id",
        "loan_amnt", "funded_amnt", "int_rate", "installment",
        "annual_inc", "dti", "total_pymnt", "total_rec_prncp",
        "total_rec_int", "recoveries", "is_default", "loan_status",
    ]
    return fact[fact_cols]


# ---------------------------------------------------------------------------
# Data quality helpers
# ---------------------------------------------------------------------------

def null_rate_report(df: pd.DataFrame) -> dict[str, float]:
    """Return the fraction of null values per column."""
    return {col: float(df[col].isna().mean()) for col in df.columns}


def row_count_assertion(df: pd.DataFrame, min_rows: int) -> None:
    """Raise AssertionError if df has fewer than min_rows rows."""
    if len(df) < min_rows:
        raise AssertionError(
            f"Expected at least {min_rows} rows, got {len(df)}."
        )
