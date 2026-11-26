# Architecture — Financial Data Warehouse Pipeline

## Data flow

ASCII overview (raw file → consumption):

```
  data/raw/lending_club_loans.csv
            ├──────────────────────────────┐
            ▼                              │
  ┌───────────────────┐                    │
  │ extract.load_raw  │                    │
  │ extract.validate  │                    │
  └─────────┬─────────┘                    │
            │                              │
            ▼                              │
  ┌───────────────────┐                    │
  │ transform.*       │  clean rates,      │
  └─────────┬─────────┘  parse dates,      │
            │            build dims + fact │
            ▼                              ▼
  ┌───────────────────┐          ┌───────────────────┐
  │ load.py           │          │ spark_transform   │
  │ DuckDB star schema│          │ (reads CSV itself)│
  └─────────┬─────────┘          │ Parquet datasets  │
            │                    └─────────┬─────────┘
            │                              │
            ▼                              ▼
  warehouse.duckdb                 data/processed/
            │                         (raw_loans, aggregates)
            ├──────────────────────────────┐
            ▼                              ▼
  sql/analytics/*.sql              dashboard/app.py
  (13 queries, CTEs / windows)     (Streamlit + Plotly)
```

## Components

1. **Extract** — `src/extract.py`: read only the `REQUIRED_COLUMNS` from the CSV (`usecols`, `low_memory=False`) and validate the schema.
2. **Transform** — `src/transform.py`: surrogate keys, `fact_loans` with FKs, `filter_valid_loan_rows` for CSV footer lines.
3. **Load** — `src/load.py`: `INSERT OR IGNORE` into DuckDB tables.
4. **Orchestration** — `src/pipeline.py`: extract → quality report → transform → validate fact table → (one transaction: DDL → load → verify row counts → commit).
5. **Spark** — `src/spark_transform.py`: optional Parquet extracts for large-scale practice (requires JVM).
6. **Analytics** — `sql/analytics/`: DuckDB-ready SQL for ad-hoc analysis.
7. **Dashboard** — `dashboard/app.py`: reads `warehouse.duckdb` (or `DUCKDB_PATH`).

## Schema

One fact table (`fact_loans`) with foreign keys to four dimensions (`dim_borrower`, `dim_loan_grade`, `dim_time`, `dim_purpose`). The full DDL, with a comment on each table, is in `sql/schema/create_tables.sql`.
