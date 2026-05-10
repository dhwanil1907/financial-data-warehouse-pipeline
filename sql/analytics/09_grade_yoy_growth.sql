-- Year-over-year loan volume by grade (LAG partitioned by grade).
WITH vol AS (
    SELECT t.year,
           g.grade,
           COUNT(*) AS loan_vol
    FROM fact_loans AS f
    INNER JOIN dim_time AS t ON f.time_id = t.time_id
    INNER JOIN dim_loan_grade AS g ON f.grade_id = g.grade_id
    GROUP BY t.year,
             g.grade
),
yoy AS (
    SELECT year,
           grade,
           loan_vol,
           LAG(loan_vol) OVER (PARTITION BY grade ORDER BY year) AS prior_year_vol
    FROM vol
)
SELECT year,
       grade,
       loan_vol,
       prior_year_vol,
       CASE
           WHEN prior_year_vol IS NULL OR prior_year_vol = 0 THEN NULL
           ELSE (loan_vol - prior_year_vol) * 1.0 / prior_year_vol
       END AS yoy_growth
FROM yoy
ORDER BY grade,
         year;
