-- Monthly default rate and rolling 3-month average (ROWS window).
WITH monthly AS (
    SELECT t.year,
           t.month,
           AVG(CAST(f.is_default AS DOUBLE)) AS month_default_rate
    FROM fact_loans AS f
    INNER JOIN dim_time AS t ON f.time_id = t.time_id
    GROUP BY t.year,
             t.month
),
seq AS (
    SELECT year,
           month,
           month_default_rate,
           ROW_NUMBER() OVER (ORDER BY year, month) AS seq
    FROM monthly
)
SELECT year,
       month,
       month_default_rate,
       AVG(month_default_rate) OVER (
           ORDER BY seq ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
       ) AS rolling_3m_default_rate
FROM seq
ORDER BY year,
         month;
