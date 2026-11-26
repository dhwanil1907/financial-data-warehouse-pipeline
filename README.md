# Financial Data Warehouse Pipeline

End-to-end **Lending Club** loan data pipeline: raw CSV → star-schema DuckDB warehouse → SQL analytics and an interactive Streamlit dashboard, with an optional PySpark → Parquet path.

**Stack:** Python 3.11 · pandas · DuckDB · PySpark · Streamlit · Plotly · pytest · uv · ruff

**Dataset:** [Kaggle — Lending Club Loan Data](https://www.kaggle.com/datasets/wordsforthewise/lending-club) (~2.26M loans, 2007–2018). Place `accepted_2007_to_2018Q4.csv` at `data/raw/lending_club_loans.csv`.

**Repo:** [github.com/dhwanil1907/financial-data-warehouse-pipeline](https://github.com/dhwanil1907/financial-data-warehouse-pipeline)

**Docs:** [docs/concepts.md](docs/concepts.md) · [docs/architecture.md](docs/architecture.md)
---

## Features

- Schema validation and data-quality checks that fail the run: required columns, null keys, repeated loan IDs
- Star schema (1 fact + 4 dimensions) with surrogate keys, loaded in one transaction with row-count verification, so a failed run leaves the previous warehouse intact
- 13 analytical SQL queries using CTEs and window functions
- Streamlit dashboard with 4 Plotly charts
- Optional PySpark aggregations written to Parquet
- pytest suite (39 passing) and reproducible setup via uv

## Warehouse tables

| Table | Rows |
|---|---|
| `fact_loans` | 2,260,668 |
| `dim_borrower` | 90,211 |
| `dim_loan_grade` | 35 |
| `dim_purpose` | 28 |
| `dim_time` | 139 |

## Key metrics

| Metric | Value |
|---|---|
| Loans analyzed | 2,260,668 |
| Resolved loans (Fully Paid or defaulted) | 1,348,099 |
| Overall default rate (resolved loans) | 19.98% |
| Loan amount range | $500 – $40,000 |
| Average loan amount | ≈ $15,047 |

**Default definition:** `is_default` is TRUE for Charged Off, Default and the "Does not meet the credit policy" Charged Off status, FALSE for Fully Paid, and NULL for loans still in progress (Current, Late, In Grace Period). Rates are averaged over resolved loans only, so in-progress loans don't dilute them.

Default rate by loan grade (`sql/analytics/01_default_rate_by_grade.sql`):

| Grade | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| Default rate | 6.04% | 13.40% | 22.44% | 30.38% | 38.43% | 45.15% | 49.67% |

Default risk rises monotonically from grade A to G — roughly 8× higher for G than A.

---

## Quick start

```bash
uv sync
```

### 1. Load the DuckDB warehouse

```bash
uv run python -m src.pipeline --csv data/raw/lending_club_loans.csv --db warehouse.duckdb
```

Expected output:
```
dim_borrower:  90,211
dim_loan_grade:    35
dim_purpose:       28
dim_time:         139
fact_loans: 2,260,668
```

### 2. Launch the dashboard

```bash
uv run streamlit run dashboard/app.py
```

Open **http://localhost:8501**. Uses `warehouse.duckdb` by default — override with `DUCKDB_PATH=/path/to/db`.

**DuckDB lock:** do not run the ETL pipeline and the dashboard against the same `.duckdb` file at the same time. Finish (or stop) the pipeline before opening Streamlit, or you will get a conflicting-lock `IOException`.

### 3. Run tests

```bash
uv run pytest tests/ -v
```

39 pass; the 5 Spark tests are skipped unless Spark can start (needs JDK 17 or 21).

### 4. SQL analytics (ad-hoc)

```bash
duckdb warehouse.duckdb < sql/analytics/01_default_rate_by_grade.sql
```

All 13 queries are in `sql/analytics/`.

### 5. Spark → Parquet (optional, requires JDK 17 or 21)

```bash
uv run python -m src.spark_transform --csv data/raw/lending_club_loans.csv --output-dir data/processed
```

Writes `data/processed/raw_loans/`, `default_rate_by_grade/`, `avg_loan_by_year/`.

---

## Architecture

```
data/raw/lending_club_loans.csv
          │
    ┌─────┴──────────────────────┐
    ▼                            ▼
┌──────────────┐        ┌─────────────────────┐
│  extract.py  │        │ spark_transform.py  │  (optional, needs JVM;
│ validate     │        │ reads the CSV       │   separate path)
│ schema       │        │ directly → Parquet  │
└──────┬───────┘        └─────────────────────┘
       │
       ▼
┌──────────────┐
│ transform.py │  drop footer rows, build dim + fact DataFrames, surrogates
└──────┬───────┘
       │
       ▼
┌──────────┐
│  load.py │  one transaction, row counts verified
│ → DuckDB │
└────┬─────┘
     │
     ▼
warehouse.duckdb
     │
  ┌──┴──────────────────┐
  ▼                     ▼
sql/analytics/     dashboard/app.py
(13 SQL files)     (Streamlit + Plotly)
```

See [docs/architecture.md](docs/architecture.md) for the full data-flow write-up.

---

## Project layout

```
├── src/
│   ├── pipeline.py          # ETL orchestrator (CLI: --csv, --db)
│   ├── extract.py           # CSV load + schema validation
│   ├── transform.py         # dim/fact builders, data quality helpers
│   ├── load.py              # DuckDB INSERT OR IGNORE helpers
│   ├── db.py                # DuckDB connection + DDL runner
│   └── spark_transform.py   # PySpark aggregations + Parquet writer
├── sql/
│   ├── schema/
│   │   └── create_tables.sql  # Star schema DDL (5 tables)
│   └── analytics/             # 13 analytical queries (CTEs + window fns), see its README
├── dashboard/
│   └── app.py               # Streamlit dashboard (4 Plotly charts)
├── docs/
│   ├── architecture.md      # Data-flow write-up
│   └── concepts.md          # Concepts used in this project
├── tests/                   # pytest suite (39 passing)
├── data/
│   ├── raw/                  # lending_club_loans.csv (gitignored)
│   └── processed/            # Parquet output from Spark (gitignored)
├── pyproject.toml           # dependencies and Python version
├── uv.lock                  # locked dependency versions
├── .python-version          # Python 3.11 for uv
└── .gitignore / .gitattributes
```
