-- Default rate by loan purpose.
WITH loans AS (
    SELECT f.is_default,
           p.purpose
    FROM fact_loans AS f
    INNER JOIN dim_purpose AS p ON f.purpose_id = p.purpose_id
),
agg AS (
    SELECT purpose,
           AVG(CAST(is_default AS DOUBLE)) AS default_rate,
           COUNT(*) AS loan_count
    FROM loans
    GROUP BY purpose
)
SELECT purpose,
       default_rate,
       loan_count
FROM agg
ORDER BY default_rate DESC;
