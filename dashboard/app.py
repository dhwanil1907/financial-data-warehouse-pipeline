"""
Streamlit dashboard — Lending Club star schema in DuckDB.

Run from project root:
  uv run streamlit run dashboard/app.py

Optional: DUCKDB_PATH=/path/to/warehouse.duckdb
"""
from __future__ import annotations

import os
from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st

ALLOWED_GRADES = frozenset("ABCDEFG")


def _db_path() -> str:
    return os.environ.get("DUCKDB_PATH", str(Path.cwd() / "warehouse.duckdb"))


@st.cache_resource
def get_connection() -> duckdb.DuckDBPyConnection:
    path = _db_path()
    if not Path(path).is_file():
        raise FileNotFoundError(f"DuckDB file not found: {path}")
    return duckdb.connect(path, read_only=True)


def _year_bounds(con: duckdb.DuckDBPyConnection) -> tuple[int, int]:
    row = con.execute("SELECT MIN(year), MAX(year) FROM dim_time").fetchone()
    y_min, y_max = int(row[0]), int(row[1])
    if y_min > y_max:
        return 2007, 2018
    return y_min, y_max


def _grade_filter_sql(grades: list[str]) -> str:
    valid = [g for g in grades if g in ALLOWED_GRADES]
    if not valid or len(valid) == len(ALLOWED_GRADES):
        return "TRUE"
    inner = ",".join(f"'{g}'" for g in valid)
    return f"g.grade IN ({inner})"


def _term_filter_sql(term: str) -> str:
    if term == "All":
        return "TRUE"
    if term == "36 months":
        return "p.term = '36 months'"
    if term == "60 months":
        return "p.term = '60 months'"
    return "TRUE"


def _base_from() -> str:
    return """
        FROM fact_loans AS f
        INNER JOIN dim_loan_grade AS g ON f.grade_id = g.grade_id
        INNER JOIN dim_time AS t ON f.time_id = t.time_id
        INNER JOIN dim_purpose AS p ON f.purpose_id = p.purpose_id
        INNER JOIN dim_borrower AS b ON f.borrower_id = b.borrower_id
    """


def main() -> None:
    st.set_page_config(
        page_title="Lending Club Portfolio Analytics",
        layout="wide",
    )
    st.title("Lending Club Portfolio Analytics")

    try:
        con = get_connection()
    except FileNotFoundError as err:
        st.error(str(err))
        st.stop()

    y_lo, y_hi = _year_bounds(con)

    with st.sidebar:
        st.header("Filters")
        year_range = st.slider("Issue year range", y_lo, y_hi, (y_lo, y_hi))
        grades = st.multiselect(
            "Loan grade",
            options=sorted(ALLOWED_GRADES),
            default=sorted(ALLOWED_GRADES),
        )
        term = st.selectbox("Term", ["All", "36 months", "60 months"], index=0)

    grade_sql = _grade_filter_sql(grades)
    term_sql = _term_filter_sql(term)
    common_where = f"""
        t.year BETWEEN {int(year_range[0])} AND {int(year_range[1])}
        AND ({grade_sql})
        AND ({term_sql})
    """

    kpi_sql = f"""
        SELECT
            COUNT(*) AS n_loans,
            AVG(f.loan_amnt) / 1000.0 AS avg_loan_k,
            AVG(CAST(f.is_default AS DOUBLE)) * 100.0 AS default_pct,
            SUM(f.funded_amnt) / 1e9 AS funded_b
        {_base_from()}
        WHERE {common_where}
    """
    kpi = con.execute(kpi_sql).fetchdf().iloc[0]
    if int(kpi["n_loans"]) == 0:
        st.warning("No loans match the current filters.")
        st.stop()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total loans", f"{int(kpi['n_loans']):,}")
    c2.metric("Avg loan size ($K)", f"{kpi['avg_loan_k']:.1f}")
    c3.metric("Default rate (%)", f"{kpi['default_pct']:.2f}")
    c4.metric("Total funded ($B)", f"{kpi['funded_b']:.2f}")

    st.subheader("Default rate by grade")
    q_grade = f"""
        SELECT g.grade,
               AVG(CAST(f.is_default AS DOUBLE)) * 100.0 AS default_rate_pct
        {_base_from()}
        WHERE {common_where}
        GROUP BY g.grade
        ORDER BY g.grade
    """
    df_grade = con.execute(q_grade).fetchdf()
    if df_grade.empty:
        st.info("No grade-level rows for these filters.")
    else:
        fig1 = px.bar(
            df_grade,
            x="default_rate_pct",
            y="grade",
            orientation="h",
            color="default_rate_pct",
            color_continuous_scale="Reds",
            labels={"default_rate_pct": "Default rate (%)", "grade": "Grade"},
        )
        st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Annual funded volume")
    q_year = f"""
        SELECT t.year,
               SUM(f.funded_amnt) / 1e9 AS funded_b
        {_base_from()}
        WHERE {common_where}
        GROUP BY t.year
        ORDER BY t.year
    """
    df_year = con.execute(q_year).fetchdf()
    if df_year.empty:
        st.info("No yearly funded volume for these filters.")
    else:
        fig2 = px.area(
            df_year,
            x="year",
            y="funded_b",
            labels={"year": "Year", "funded_b": "Funded ($B)"},
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Default rate by home ownership")
    q_home = f"""
        SELECT b.home_ownership,
               AVG(CAST(f.is_default AS DOUBLE)) * 100.0 AS default_rate_pct
        {_base_from()}
        WHERE {common_where}
          AND b.home_ownership IN ('RENT', 'OWN', 'MORTGAGE')
        GROUP BY b.home_ownership
        ORDER BY b.home_ownership
    """
    df_home = con.execute(q_home).fetchdf()
    if df_home.empty:
        st.info("No home-ownership rows for these filters.")
    else:
        fig3 = px.bar(
            df_home,
            x="home_ownership",
            y="default_rate_pct",
            barmode="group",
            color="home_ownership",
            labels={
                "default_rate_pct": "Default rate (%)",
                "home_ownership": "Home ownership",
            },
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Top 10 purposes by funded volume")
    q_purpose = f"""
        WITH ranked AS (
            SELECT p.purpose,
                   SUM(f.funded_amnt) AS total_funded,
                   RANK() OVER (ORDER BY SUM(f.funded_amnt) DESC) AS rnk
            {_base_from()}
            WHERE {common_where}
            GROUP BY p.purpose
        )
        SELECT purpose, total_funded
        FROM ranked
        WHERE rnk <= 10
        ORDER BY rnk
    """
    df_purpose = con.execute(q_purpose).fetchdf()
    if df_purpose.empty:
        st.info("No purpose breakdown for these filters.")
    else:
        fig4 = px.pie(
            df_purpose,
            names="purpose",
            values="total_funded",
            hole=0.45,
        )
        st.plotly_chart(fig4, use_container_width=True)


if __name__ == "__main__":
    main()
