# Financial Data Warehouse Pipeline

End-to-end **Lending Club** loan data pipeline: raw CSV → validated extract → pandas transform (star schema keys) → **DuckDB** warehouse → optional **PySpark** Parquet analytics → **Streamlit** dashboard. Includes **13 SQL analytics** queries (CTEs and window functions).

**Dataset:** [Kaggle — Lending Club Loan Data](https://www.kaggle.com/datasets/wordsforthewise/lending-club) — place `accepted_2007_to_2018Q4.csv` (or a symlink) at `data/raw/lending_club_loans.csv`.

## Quick start

```bash
cd "Financial Data Warehouse Pipeline"
uv sync
```

### 1. Load the warehouse (DuckDB)

```bash
uv run python -m src.pipeline --csv data/raw/lending_club_loans.csv --db warehouse.duckdb
```

Expect on the full dataset roughly **2.26M** rows in `fact_loans` and **35** rows in `dim_loan_grade`. Footer/summary lines in the CSV are dropped automatically.

### 2. Run tests

```bash
uv run pytest tests/ -v
```

**PySpark tests** need a **JDK** on `PATH` (`java -version`). If Java is missing, those tests are skipped.

### 3. Spark → Parquet (optional)

Requires Java (JDK 17+ recommended).

```bash
uv run python -m src.spark_transform --csv data/raw/lending_club_loans.csv --output-dir data/processed
```

Outputs: `data/processed/raw_loans/`, `default_rate_by_grade/`, `avg_loan_by_year/`.

### 4. SQL analytics

Point DuckDB at the warehouse file and run any file under `sql/analytics/`, for example:

```bash
duckdb warehouse.duckdb < sql/analytics/01_default_rate_by_grade.sql
```

### 5. Dashboard

```bash
uv run streamlit run dashboard/app.py
```

Open **http://localhost:8501**. Set `DUCKDB_PATH` if the database is not `./warehouse.duckdb`.

---

## Architecture (ASCII)

```
                    ┌─────────────────┐
                    │  Kaggle CSV     │
                    │  (raw loans)    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  extract.py     │  schema validation
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ transform.py    │  dims + fact DataFrames
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
     ┌─────────────────┐          ┌─────────────────┐
     │  load.py        │          │ spark_transform │  (needs Java)
     │  → DuckDB       │          │  → Parquet      │
     └────────┬────────┘          └────────┬────────┘
              │                             │
              ▼                             ▼
     ┌─────────────────┐          data/processed/
     │ warehouse.duckdb│          *.parquet
     └────────┬────────┘
              │
     ┌────────┴────────┐
     ▼                 ▼
┌─────────────┐  ┌─────────────┐
│ sql/analytics│  │ Streamlit   │
│ 13 queries   │  │ dashboard   │
└─────────────┘  └─────────────┘
```

---

## Project layout (partial)

| Path | Role |
|------|------|
| `src/pipeline.py` | ETL CLI (`--csv`, `--db`) |
| `src/spark_transform.py` | Spark aggregations + CLI |
| `schema/create_tables.sql` | Star schema DDL |
| `sql/analytics/*.sql` | Analytical queries |
| `dashboard/app.py` | Streamlit UI |

---

## ERD

See `schema/erd_notes.md` and paste the dbdiagram.io block at **https://dbdiagram.io/d** for a diagram.
