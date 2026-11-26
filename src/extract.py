"""
Extract layer — loads the raw Lending Club CSV and validates its schema.

Public API:
    REQUIRED_COLUMNS  list[str]   columns that must be present in the CSV
    load_raw_csv(path)            read CSV → DataFrame
    validate_schema(df)           raise ValueError if schema is invalid
"""
import pandas as pd

REQUIRED_COLUMNS: list[str] = [
    "id",
    "addr_state",
    "zip_code",
    "home_ownership",
    "emp_length",
    "verification_status",
    "annual_inc",
    "issue_d",
    "loan_status",
    "loan_amnt",
    "funded_amnt",
    "int_rate",
    "installment",
    "grade",
    "sub_grade",
    "purpose",
    "term",
    "dti",
    "total_pymnt",
    "total_rec_prncp",
    "total_rec_int",
    "recoveries",
]


def load_raw_csv(path: str) -> pd.DataFrame:
    """Read the Lending Club CSV and return a DataFrame of the required columns.

    The raw file has ~150 columns but the pipeline uses only REQUIRED_COLUMNS,
    so the rest are skipped at read time to save memory. A callable ``usecols``
    (rather than a list) lets a missing column through, so validate_schema can
    report it instead of pandas raising a less helpful error.

    Uses low_memory=False to prevent mixed-type inference warnings on the
    large (~2.26M row) dataset.
    """
    return pd.read_csv(path, usecols=lambda col: col in REQUIRED_COLUMNS, low_memory=False)


def validate_schema(df: pd.DataFrame) -> None:
    """Raise ValueError if df is empty or missing any required column.

    Args:
        df: raw DataFrame produced by load_raw_csv.

    Raises:
        ValueError: if df has zero rows or any REQUIRED_COLUMNS entry is absent.
    """
    if df.empty:
        raise ValueError("DataFrame is empty — no rows loaded from CSV.")

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
