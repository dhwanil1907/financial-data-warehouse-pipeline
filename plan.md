# Financial Data Warehouse Pipeline — Implementation Plan

**Goal:** Build an end-to-end financial data warehouse over the Lending Club loan dataset (~2.26M records) — star schema in DuckDB, Python ETL with data quality checks, Spark aggregation layer, SQL analytics with window functions/CTEs, and a Streamlit dashboard.

**Architecture:** Raw CSV → `extract.py` validates & loads → `transform.py` cleans & builds dimension keys → `spark_transform.py` runs heavy aggregations and writes Parquet → `load.py` inserts into DuckDB star schema → SQL analytics layer → Streamlit dashboard queries DuckDB directly.

**Tech Stack:** Python 3.11+, DuckDB 0.10+, PySpark 3.5+, pandas 2.x, Streamlit 1.x, Plotly, pytest, uv, ruff

---

## Dataset

Download: [Lending Club Loan Data](https://www.kaggle.com/datasets/wordsforthewise/lending-club) — accepted loans 2007–2018 — `accepted_2007_to_2018Q4.csv` (~2.26M rows).

Place at: `data/raw/lending_club_loans.csv`

| Column | Type | Description |
|---|---|---|
| `id` | str | Loan identifier |
| `addr_state` | str | Borrower state (2-char) |
| `zip_code` | str | 3-digit zip prefix (e.g. `900xx`) |
| `home_ownership` | str | RENT / OWN / MORTGAGE / OTHER |
| `emp_length` | str | Employment length (`10+ years`, `< 1 year`, etc.) |
| `verification_status` | str | Income verification status |
| `annual_inc` | float | Annual income |
| `issue_d` | str | Loan issue date (`Jan-2015` format) |
| `loan_status` | str | `Charged Off` = default, `Fully Paid` = paid |
| `loan_amnt` | float | Requested loan amount |
| `funded_amnt` | float | Funded amount |
| `int_rate` | str | Interest rate string (`15.99%`) |
| `installment` | float | Monthly installment |
| `grade` | str | LC grade A–G |
| `sub_grade` | str | LC sub-grade A1–G5 |
| `purpose` | str | Loan purpose (debt_consolidation, credit_card, etc.) |
| `term` | str | ` 36 months` or ` 60 months` |
| `dti` | float | Debt-to-income ratio |
| `total_pymnt` | float | Total payment received |
| `total_rec_prncp` | float | Principal received |
| `total_rec_int` | float | Interest received |
| `recoveries` | float | Post charge-off recoveries |

---

## File Structure

    financial-data-warehouse/
    ├── data/
    │   ├── raw/                     # lending_club_loans.csv goes here
    │   └── processed/               # Parquet output from Spark
    ├── schema/
    │   ├── create_tables.sql        # DDL for all 5 star schema tables
    │   └── erd_notes.md             # ERD description + dbdiagram.io source
    ├── src/
    │   ├── db.py                    # DuckDB connection helper
    │   ├── extract.py               # Load CSV + schema validation
    │   ├── transform.py             # Clean + build dimension keys
    │   ├── spark_transform.py       # PySpark aggregations → Parquet
    │   ├── load.py                  # Insert into DuckDB star schema
    │   └── pipeline.py              # ETL orchestrator (extract → transform → load)
    ├── sql/
    │   ├── ddl/
    │   │   └── star_schema.sql
    │   └── analytics/
    │       ├── 01_default_rate_by_grade.sql
    │       ├── 02_default_rate_by_year.sql
    │       ├── 03_default_rate_by_purpose.sql
    │       ├── 04_mom_loan_volume.sql
    │       ├── 05_top10_purposes_by_volume.sql
    │       ├── 06_rolling_3month_default_rate.sql
    │       ├── 07_cohort_analysis.sql
    │       ├── 08_avg_rate_by_state.sql
    │       ├── 09_grade_yoy_growth.sql
    │       ├── 10_term_vs_default_rate.sql
    │       ├── 11_home_ownership_comparison.sql
    │       ├── 12_dti_impact_on_default.sql
    │       └── 13_verification_status_impact.sql
    ├── dashboard/
    │   └── app.py                   # Streamlit app
    ├── tests/
    │   ├── conftest.py              # Shared fixtures (sample DataFrame, DuckDB in-memory)
    │   ├── test_db.py
    │   ├── test_extract.py
    │   ├── test_transform.py
    │   ├── test_load.py
    │   └── test_spark_transform.py
    ├── docs/
    │   └── architecture.md          # Pipeline diagram + ERD link
    ├── pyproject.toml
    ├── README.md
    └── plan.md

---

## Star Schema

Five tables: one fact table and four dimension tables.

**dim_borrower** — deduplicates on (addr_state, zip_code, home_ownership, emp_length, verification_status). Captures borrower profile segments, not individual identity.

**dim_loan_grade** — one row per (grade, sub_grade) combination. Maximum 35 rows (A1–G5).

**dim_time** — one row per unique issue month. Derived from `issue_d` parsed as `Jan-2015` format. Adds year, month, quarter.

**dim_purpose** — one row per (purpose, term) combination. ~30 combinations.

**fact_loans** — one row per loan. Foreign keys to all four dimensions. Stores loan_amnt, funded_amnt, int_rate (as double, % stripped), installment, annual_inc, dti, term_months, total_pymnt, total_rec_prncp, total_rec_int, recoveries, is_default (TRUE when loan_status = `Charged Off`), and loan_status.

---

## Task 1: Project Bootstrap

- [ ] Initialize uv project with Python 3.11 and add all dependencies: duckdb, pandas, pyspark, streamlit, plotly, pytest, ruff, pytest-cov.
- [ ] Create directory skeleton: `data/raw`, `data/processed`, `schema`, `src`, `sql/ddl`, `sql/analytics`, `dashboard`, `tests`, `docs`.
- [ ] Add `__init__.py` to `src/`, `tests/`, and `dashboard/`.
- [ ] Create `.gitignore` excluding `data/raw/*.csv`, `data/processed/`, `*.duckdb`, `__pycache__/`, `.venv/`.
- [ ] Commit: `chore: initialize project structure`.

---

## Task 2: Star Schema DDL

- [ ] Write `schema/create_tables.sql` with CREATE TABLE IF NOT EXISTS statements for all five tables: `dim_borrower`, `dim_loan_grade`, `dim_time`, `dim_purpose`, `fact_loans`.
- [ ] Write `schema/erd_notes.md` with normalization notes and dbdiagram.io source to visualize the schema.
- [ ] Copy the DDL to `sql/ddl/star_schema.sql`.
- [ ] Commit: `feat: add star schema DDL and ERD notes`.

---

## Task 3: DuckDB Connection Helper

- [ ] Write failing tests in `tests/test_db.py`: verify `get_connection` returns a DuckDB connection, verify `execute_ddl` creates all five tables.
- [ ] Implement `src/db.py` with `get_connection(db_path)` and `execute_ddl(con, ddl_path)`.
- [ ] Run tests — expect 2 passed.
- [ ] Commit: `feat: add DuckDB connection helper with tests`.

---

## Task 4: Extract Layer

- [ ] Write failing tests in `tests/test_extract.py`: loading a CSV returns a DataFrame with correct row count, `validate_schema` passes on valid data, raises `ValueError` on missing columns, raises `ValueError` on empty DataFrame, `REQUIRED_COLUMNS` contains `id`, `loan_status`, `grade`, `loan_amnt`.
- [ ] Implement `src/extract.py` with `REQUIRED_COLUMNS` list, `load_raw_csv(path)` using `low_memory=False`, and `validate_schema(df)`.
- [ ] Run tests — expect 6 passed.
- [ ] Commit: `feat: add extract layer with schema validation`.

---

## Task 5: Transform Layer

- [ ] Write failing tests in `tests/test_transform.py` covering: `clean_rate_column` strips `%` and casts to float, `parse_issue_date` parses `Jan-2015` format, `parse_term_months` extracts integer from ` 36 months`, each `build_dim_*` function deduplicates correctly and produces the right columns, `build_fact_table` sets `is_default=True` for `Charged Off` rows and `is_default=False` for `Fully Paid` rows, `int_rate` in fact is float dtype, null rate report returns 0.0 for clean fixture data.
- [ ] Implement `src/transform.py` with: `clean_rate_column`, `parse_issue_date`, `parse_term_months`, `build_dim_borrower`, `build_dim_loan_grade`, `build_dim_time`, `build_dim_purpose`, `build_fact_table`, `null_rate_report`, `row_count_assertion`.
- [ ] Run tests — expect 11 passed.
- [ ] Commit: `feat: add transform layer with dim/fact builders and data quality checks`.

---

## Task 6: Load Layer

- [ ] Write failing tests in `tests/test_load.py` covering: `load_dimension` inserts rows, `load_dimension` is idempotent (no duplicates on re-run), `load_fact` inserts rows into `fact_loans`, `get_row_counts` returns a dict with all table names.
- [ ] Implement `src/load.py` with `load_dimension(con, df, table_name)` using INSERT OR IGNORE on primary key, `load_fact(con, df)`, and `get_row_counts(con)`.
- [ ] Run full test suite — all tests pass.
- [ ] Commit: `feat: add load layer with idempotent inserts`.

---

## Task 7: ETL Orchestration Pipeline

- [ ] Implement `src/pipeline.py` that chains extract → transform → load with a CLI interface (`--csv` and `--db` arguments).
- [ ] Print a data quality report before transform showing null rates for key columns (`id`, `loan_status`, `grade`, `loan_amnt`, `int_rate`, `addr_state`, `issue_d`). Flag any column with > 5% nulls.
- [ ] Print final row counts for all five tables after load.
- [ ] Run the pipeline against the real CSV once it is downloaded. Expected counts: ~2.26M rows in `fact_loans`, ~35 rows in `dim_loan_grade`.
- [ ] Commit: `feat: add ETL orchestration pipeline with data quality reporting`.

---

## Task 8: Spark Transformation Layer

- [ ] Write failing tests in `tests/test_spark_transform.py` covering: `create_spark_session` returns a SparkSession, `compute_default_rate_by_grade` returns a DataFrame with `grade` and `default_rate` columns where rates are between 0 and 1, `compute_avg_loan_by_year` returns a DataFrame with `issue_year` and `avg_loan_amount` columns, `write_parquet` creates `.parquet` files at the output path.
- [ ] Implement `src/spark_transform.py` with: `create_spark_session`, `compute_default_rate_by_grade` (group by grade, compute default rate), `compute_avg_loan_by_year` (parse year from `issue_d`, group and average `loan_amnt`), `write_parquet`, and `run_spark_pipeline` CLI entry point.
- [ ] Run tests — expect 5 passed (Spark startup takes ~15s).
- [ ] Run against real data to write Parquet to `data/processed/` — outputs: `raw_loans/`, `default_rate_by_grade/`, `avg_loan_by_year/`.
- [ ] Commit: `feat: add Spark aggregation layer with grade/year analytics`.

---

## Task 9: SQL Analytics Layer

Write 13 standalone SQL files in `sql/analytics/`, each joinable against the DuckDB warehouse. All use window functions or CTEs.

- [ ] `01_default_rate_by_grade.sql` — default rate grouped by LC grade A–G, ordered by rate descending.
- [ ] `02_default_rate_by_year.sql` — default rate by issue year from `dim_time`.
- [ ] `03_default_rate_by_purpose.sql` — default rate by loan purpose (debt_consolidation, credit_card, etc.).
- [ ] `04_mom_loan_volume.sql` — month-over-month loan count and funded volume using LAG window function.
- [ ] `05_top10_purposes_by_volume.sql` — top 10 purposes by total funded amount, with RANK window function.
- [ ] `06_rolling_3month_default_rate.sql` — rolling 3-month default rate using ROWS BETWEEN 2 PRECEDING AND CURRENT ROW.
- [ ] `07_cohort_analysis.sql` — cohort default rates by issue year, comparing early cohorts (2007–2010) to later ones.
- [ ] `08_avg_rate_by_state.sql` — average interest rate and loan amount by borrower state, minimum 500 loans.
- [ ] `09_grade_yoy_growth.sql` — year-over-year loan volume growth by grade using LAG partitioned by grade.
- [ ] `10_term_vs_default_rate.sql` — default rate comparison between 36-month and 60-month loans.
- [ ] `11_home_ownership_comparison.sql` — default rate and avg loan by home ownership type (RENT / OWN / MORTGAGE).
- [ ] `12_dti_impact_on_default.sql` — default rate segmented into DTI quartiles using NTILE(4).
- [ ] `13_verification_status_impact.sql` — default rate and avg interest rate by income verification status.
- [ ] Verify all 13 queries run against the warehouse without errors.
- [ ] Commit: `feat: add 13 SQL analytics queries with window functions and CTEs`.

---

## Task 10: Streamlit Dashboard

- [ ] Implement `dashboard/app.py` with page title "Lending Club Portfolio Analytics", wide layout.
- [ ] Sidebar filters: year range slider (from `dim_time`), multiselect for loan grade (A–G), selectbox for term (All / 36 months / 60 months).
- [ ] KPI row (4 columns): Total Loans, Avg Loan Size ($K), Default Rate (%), Total Funded ($B).
- [ ] Chart 1: Default rate by grade — horizontal bar chart, color-scaled red.
- [ ] Chart 2: Annual funded volume trend — area chart by issue year.
- [ ] Chart 3: Home ownership default comparison — grouped bar chart (RENT / OWN / MORTGAGE).
- [ ] Chart 4: Top 10 purposes by funded volume — donut chart.
- [ ] All chart queries respect sidebar filters via parameterized SQL fragments.
- [ ] Run dashboard and verify it opens at `http://localhost:8501`.
- [ ] Commit: `feat: add Streamlit dashboard with 4 Plotly charts and sidebar filters`.

---

## Task 11: README + Architecture Docs

- [ ] Write `README.md` with project description, quick-start commands (uv sync, download dataset, run pipeline, run Spark, launch dashboard), architecture diagram (ASCII), and links to Kaggle dataset.
- [ ] Write `docs/architecture.md` with ASCII pipeline diagram showing data flow from raw CSV through extract, transform, Spark, load, DuckDB, and Streamlit, plus a link to the dbdiagram.io ERD.
- [ ] Commit: `docs: add README and architecture documentation`.

---

## Task 12: Final Validation

- [ ] Run full test suite (`uv run pytest tests/ -v`) — all tests pass.
- [ ] Run ETL pipeline end-to-end against real data — row counts match expectations.
- [ ] Run Spark pipeline — Parquet files present in `data/processed/`.
- [ ] Run all 13 SQL analytics queries — all return rows without error.
- [ ] Launch dashboard — all 4 charts render with correct data.
- [ ] Commit: `chore: final validation pass`.
