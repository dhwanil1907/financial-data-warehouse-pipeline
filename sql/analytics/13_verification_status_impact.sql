-- Default rate and average interest rate by income verification status.
WITH joined AS (
    SELECT b.verification_status,
           f.int_rate,
           CAST(f.is_default AS DOUBLE) AS is_def
    FROM fact_loans AS f
    INNER JOIN dim_borrower AS b ON f.borrower_id = b.borrower_id
),
agg AS (
    SELECT verification_status,
           AVG(is_def) AS default_rate,
           AVG(int_rate) AS avg_int_rate,
           COUNT(*) AS n_loans
    FROM joined
    GROUP BY verification_status
)
SELECT verification_status,
       default_rate,
       avg_int_rate,
       n_loans,
       RANK() OVER (ORDER BY default_rate DESC) AS risk_rank
FROM agg
ORDER BY default_rate DESC;
