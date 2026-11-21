# Analytics queries

Thirteen queries over the star schema in `warehouse.duckdb`. Run any of them with:

```bash
duckdb warehouse.duckdb < sql/analytics/01_default_rate_by_grade.sql
```

Default rates are averaged over **resolved loans only** (Fully Paid or defaulted). Loans still in progress have `is_default = NULL` and are excluded.

| # | Query | Question it answers | Technique |
|---|---|---|---|
| 01 | `01_default_rate_by_grade.sql` | How does default rate change from grade A to G? | CTE, join |
| 02 | `02_default_rate_by_year.sql` | How does default rate vary by issue year? | CTE, join |
| 03 | `03_default_rate_by_purpose.sql` | Which loan purposes default most? | CTE, join |
| 04 | `04_mom_loan_volume.sql` | How do monthly loan count and funded volume change month over month? | `LAG` |
| 05 | `05_top10_purposes_by_volume.sql` | Which 10 purposes receive the most funding? | `RANK` |
| 06 | `06_rolling_3month_default_rate.sql` | What is the monthly default rate and its rolling 3-month average? | `ROWS BETWEEN` window |
| 07 | `07_cohort_analysis.sql` | Do early (2007–2010) and later cohorts default differently? | `CASE` cohorts |
| 08 | `08_avg_rate_by_state.sql` | What are average interest rate and loan size by state (min 500 loans)? | `HAVING`, `RANK` |
| 09 | `09_grade_yoy_growth.sql` | How does loan volume grow year over year within each grade? | `LAG` with `PARTITION BY` |
| 10 | `10_term_vs_default_rate.sql` | Do 60-month loans default more than 36-month loans? | CTE, join |
| 11 | `11_home_ownership_comparison.sql` | How do default rate and loan size differ by home ownership? | `RANK` |
| 12 | `12_dti_impact_on_default.sql` | Does a higher debt-to-income ratio mean more defaults? | `NTILE` quartiles |
| 13 | `13_verification_status_impact.sql` | How do default and interest rates differ by income verification? | `RANK` |
