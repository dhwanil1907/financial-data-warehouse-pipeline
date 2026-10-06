# Financial Data Warehouse Pipeline

End-to-end **Lending Club** loan data pipeline: raw CSV → star-schema DuckDB warehouse → SQL analytics and an interactive Streamlit dashboard, with an optional PySpark → Parquet path.

**Stack:** Python 3.11 · pandas · DuckDB · PySpark · Streamlit · Plotly · pytest · uv · ruff

**Dataset:** [Kaggle — Lending Club Loan Data](https://www.kaggle.com/datasets/wordsforthewise/lending-club) (~2.26M loans, 2007–2018). Place `accepted_2007_to_2018Q4.csv` at `data/raw/lending_club_loans.csv`.

**Repo:** [github.com/dhwanil1907/financial-data-warehouse-pipeline](https://github.com/dhwanil1907/financial-data-warehouse-pipeline)

**Docs:** [concepts.md](concepts.md) · [docs/architecture.md](docs/architecture.md) · [schema/erd_notes.md](schema/erd_notes.md)

---

## Features

- Schema validation and data-quality checks at the extract stage
- Star schema (1 fact + 4 dimensions) with surrogate keys, loaded idempotently via `INSERT OR IGNORE`
- 13 analytical SQL queries using CTEs and window functions
- Streamlit dashboard with 4 Plotly charts
- Optional PySpark aggregations written to Parquet
- pytest suite (28 passing) and reproducible setup via uv

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
| Overall default rate | 11.88% |
| Loan amount range | $500 – $40,000 |
| Average loan amount | ≈ $15,047 |

Default rate by loan grade (`sql/analytics/01_default_rate_by_grade.sql`):

| Grade | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| Default rate | 3.28% | 7.92% | 13.18% | 18.82% | 26.57% | 34.67% | 37.48% |

Default risk rises monotonically from grade A to G — roughly 11× higher for G than A.

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

28 pass, 5 Spark tests skipped unless a real JDK is on `PATH`.

### 4. SQL analytics (ad-hoc)

```bash
duckdb warehouse.duckdb < sql/analytics/01_default_rate_by_grade.sql
```

All 13 queries are in `sql/analytics/`.

### 5. Spark → Parquet (optional, requires JDK 17+)

```bash
uv run python -m src.spark_transform --csv data/raw/lending_club_loans.csv --output-dir data/processed
```

Writes `data/processed/raw_loans/`, `default_rate_by_grade/`, `avg_loan_by_year/`.

---

## Architecture

```
data/raw/lending_club_loans.csv
          │
          ▼
  ┌──────────────┐
  │  extract.py  │  validate schema, drop footer rows
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ transform.py │  build dim + fact DataFrames, surrogates
  └──────┬───────┘
         │
    ┌────┴────────────────────┐
    ▼                         ▼
┌──────────┐         ┌─────────────────────┐
│  load.py │         │ spark_transform.py  │  (optional, needs JVM)
│ → DuckDB │         │ → Parquet           │
└────┬─────┘         └─────────────────────┘
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
├── schema/
│   ├── create_tables.sql    # Star schema DDL (5 tables)
│   └── erd_notes.md         # Normalization notes + dbdiagram.io source
├── sql/
│   ├── ddl/star_schema.sql  # Same DDL as schema/create_tables.sql
│   └── analytics/           # 13 analytical queries (CTEs + window fns)
├── dashboard/
│   └── app.py               # Streamlit dashboard (4 Plotly charts)
├── tests/                   # pytest suite (28 passing)
├── concepts.md              # Concepts used in this project
├── docs/architecture.md
└── data/
    ├── raw/                  # lending_club_loans.csv (gitignored)
    └── processed/            # Parquet output from Spark (gitignored)
```

---

## ERD

See [schema/erd_notes.md](schema/erd_notes.md) — paste the dbdiagram.io block at [dbdiagram.io](https://dbdiagram.io/d) to visualise the star schema.
