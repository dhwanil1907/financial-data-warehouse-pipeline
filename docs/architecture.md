# Architecture — Financial Data Warehouse Pipeline

## Data flow

ASCII overview (raw file → consumption):

```
  data/raw/lending_club_loans.csv
            │
            ▼
  ┌───────────────────┐
  │ extract.load_raw  │
  │ extract.validate  │
  └─────────┬─────────┘
            │
            ▼
  ┌───────────────────┐
  │ transform.*       │  clean rates, parse dates, build dims + fact
  └─────────┬─────────┘
            │
            ├──────────────────────────────┐
            ▼                              ▼
  ┌───────────────────┐          ┌───────────────────┐
  │ load.py           │          │ spark_transform   │
  │ DuckDB star schema│          │ Parquet datasets  │
  └─────────┬─────────┘          └─────────┬─────────┘
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

1. **Extract** — `src/extract.py`: read CSV (`low_memory=False`), enforce `REQUIRED_COLUMNS`.
2. **Transform** — `src/transform.py`: surrogate keys, `fact_loans` with FKs, `filter_valid_loan_rows` for CSV footer lines.
3. **Load** — `src/load.py`: `INSERT OR IGNORE` into DuckDB tables.
4. **Orchestration** — `src/pipeline.py`: DDL → extract → quality report → transform → load → row counts.
5. **Spark** — `src/spark_transform.py`: optional Parquet extracts for large-scale practice (requires JVM).
6. **Analytics** — `sql/analytics/`: DuckDB-ready SQL for ad-hoc analysis.
7. **Dashboard** — `dashboard/app.py`: reads `warehouse.duckdb` (or `DUCKDB_PATH`).

## Entity relationship (ERD)

Normalization notes and a **dbdiagram.io** source block live in `schema/erd_notes.md`. Open [dbdiagram.io](https://dbdiagram.io/d) and paste the fenced block from that file to render the star schema.
