# Concepts Used in This Project

## 1. Data Warehousing

A **data warehouse** is a central repository optimised for analytical queries rather than transactional workloads. Unlike an OLTP database (many small reads/writes), a warehouse is designed for aggregations over large volumes of historical data.

**Key ideas applied here:**
- Raw source data (Lending Club CSV) is loaded once, cleaned, and stored in a structured schema optimised for analysis.
- Queries read many rows but only a few columns — DuckDB's columnar storage makes this fast.

---

## 2. Star Schema

A **star schema** organises data into one central **fact table** surrounded by **dimension tables**. The fact table holds measurable events (loans); dimension tables hold descriptive context (borrower profile, grade, time, purpose).

**Tables in this project:**

| Table | Type | Description |
|---|---|---|
| `fact_loans` | Fact | One row per loan; numeric measures + FK surrogates |
| `dim_borrower` | Dimension | Borrower segment (state, ownership, employment) |
| `dim_loan_grade` | Dimension | LC grade A–G / sub-grade A1–G5 |
| `dim_time` | Dimension | Issue month, year, quarter |
| `dim_purpose` | Dimension | Loan purpose + repayment term |

**Why star schema?**
- Simple joins — fact to dim, never dim to dim.
- Efficient aggregations — GROUP BY on small dimension columns, SUM/AVG on fact measures.
- Easy to extend — add a new dimension without touching the fact table.

---

## 3. Surrogate Keys

A **surrogate key** is a system-generated integer used as a primary key instead of the natural business key. For example, `borrower_id` replaces the five-column natural key `(addr_state, zip_code, home_ownership, emp_length, verification_status)`.

**Benefits:**
- Smaller join columns (INT vs multi-column VARCHAR).
- Stable — won't change if source data is updated.
- Required for foreign key references in fact tables.

---

## 4. ETL (Extract, Transform, Load)

**ETL** is the process of moving data from a source into a warehouse.

| Phase | Module | What it does |
|---|---|---|
| Extract | `src/extract.py` | Read CSV, validate required columns are present |
| Transform | `src/transform.py` | Clean `int_rate`, parse dates, assign surrogate keys, build dim/fact DataFrames |
| Load | `src/load.py` | `INSERT OR IGNORE` into DuckDB — idempotent, safe to re-run |

**Idempotency** means running the pipeline twice produces the same result — no duplicate rows.

---

## 5. Data Quality Checks

Before transforming, the pipeline reports **null rates** for key columns and warns if any exceed 5%. This catches upstream data issues early rather than silently loading bad data.

Applied in `src/pipeline.py` and `src/transform.py` (`null_rate_report`, `row_count_assertion`).

---

## 6. DuckDB

**DuckDB** is an embedded analytical database (like SQLite, but for analytics). It runs inside the Python process — no server, no connection pool, just a `.duckdb` file.

**Why DuckDB for this project?**
- Columnar storage → fast aggregations on wide tables.
- Native pandas integration — insert a DataFrame directly.
- Full SQL with window functions, CTEs, `DOUBLE PRECISION`, `BOOLEAN`.
- Zero infrastructure — works offline on a laptop.

---

## 7. Window Functions

**Window functions** compute a value across a sliding "window" of rows relative to the current row, without collapsing the result into one row per group (unlike `GROUP BY`).

Examples used in `sql/analytics/`:

```sql
-- LAG: compare current row to the previous one
LAG(loan_cnt) OVER (ORDER BY year, month) AS prev_loan_cnt

-- RANK: rank rows within a partition
RANK() OVER (ORDER BY total_funded DESC) AS vol_rank

-- NTILE: divide rows into equal-sized buckets
NTILE(4) OVER (ORDER BY dti) AS dti_quartile

-- Rolling average: 3-month sliding window
AVG(default_rate) OVER (
    ORDER BY seq ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
)
```

---

## 8. Common Table Expressions (CTEs)

A **CTE** (`WITH ... AS (...)`) names an intermediate result set, making complex queries readable by breaking them into named steps rather than nesting subqueries.

```sql
WITH monthly AS (
    SELECT year, month, COUNT(*) AS loan_cnt FROM ...
),
mom AS (
    SELECT *, LAG(loan_cnt) OVER (...) AS prev FROM monthly
)
SELECT * FROM mom;
```

---

## 9. PySpark

**Apache Spark** is a distributed data processing framework. **PySpark** is its Python API. In this project it is used as an optional aggregation layer that reads the raw CSV and writes summarised **Parquet** files.

**Why Spark?**
- Demonstrates the same analytics at scale — Spark can process data that doesn't fit in a single machine's RAM.
- In production, Spark would replace the pandas transform step for very large datasets.

---

## 10. Parquet

**Parquet** is a columnar binary file format designed for analytical workloads. Unlike CSV, it stores data by column, compresses efficiently, and preserves schema (types).

Used by `src/spark_transform.py` to write `data/processed/raw_loans/`, `default_rate_by_grade/`, `avg_loan_by_year/`.

---

## 11. Streamlit

**Streamlit** is a Python library that turns scripts into interactive web apps. No HTML/CSS/JS required — widgets and charts are declared in Python.

**Features used:**
- `st.set_page_config` — page title, wide layout.
- `st.sidebar` — year range slider, grade multiselect, term selectbox.
- `st.metric` — KPI cards.
- `st.plotly_chart` — Plotly charts embedded in the app.
- `@st.cache_resource` — caches the DuckDB connection across reruns.

---

## 12. Plotly Express

**Plotly Express** is a high-level charting library that produces interactive Plotly figures in one line of code.

Charts in the dashboard:
- `px.bar` — horizontal bar chart (default rate by grade, colour-scaled).
- `px.area` — area chart (annual funded volume).
- `px.bar` (grouped) — home ownership default comparison.
- `px.pie` (donut) — top 10 purposes by funded volume.

---

## 13. pytest

**pytest** is Python's standard test framework. Tests in `tests/` use:
- **Fixtures** (`conftest.py`) — reusable setup (in-memory DuckDB, sample DataFrame).
- **`tmp_path`** — pytest-provided temporary directory per test.
- **`pytest.mark.skipif`** — conditionally skip Spark tests when no JDK is present.
- **`pytest.raises`** — assert that expected exceptions are raised.

---

## 14. ruff

**ruff** is a fast Python linter written in Rust. It replaces flake8 + isort + pyupgrade in a single tool. Used here to enforce import ordering, catch unused imports, and flag style issues.

---

## 15. uv

**uv** is a fast Python package and project manager (replaces pip + virtualenv + pip-tools). `uv sync` installs all dependencies from `pyproject.toml` into a `.venv` in seconds.
