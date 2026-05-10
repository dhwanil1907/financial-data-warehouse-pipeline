-- Default rate by LC letter grade (A–G), descending by rate.
-- Uses: CTE + join star schema.
WITH loans AS (
    SELECT f.is_default,
           g.grade
    FROM fact_loans AS f
    INNER JOIN dim_loan_grade AS g ON f.grade_id = g.grade_id
),
rates AS (
    SELECT grade,
           AVG(CAST(is_default AS DOUBLE)) AS default_rate
    FROM loans
    GROUP BY grade
)
SELECT grade,
       default_rate
FROM rates
ORDER BY default_rate DESC;
