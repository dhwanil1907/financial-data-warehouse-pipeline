-- Default rate by calendar year of issue (dim_time).
WITH loans AS (
    SELECT f.is_default,
           t.year
    FROM fact_loans AS f
    INNER JOIN dim_time AS t ON f.time_id = t.time_id
)
SELECT year,
       AVG(CAST(is_default AS DOUBLE)) AS default_rate,
       COUNT(*) AS loan_count
FROM loans
GROUP BY year
ORDER BY year;
