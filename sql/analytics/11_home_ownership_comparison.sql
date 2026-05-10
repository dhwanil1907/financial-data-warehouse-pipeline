-- Default rate and average loan by home ownership (RENT / OWN / MORTGAGE).
WITH joined AS (
    SELECT b.home_ownership,
           f.loan_amnt,
           CAST(f.is_default AS DOUBLE) AS is_def
    FROM fact_loans AS f
    INNER JOIN dim_borrower AS b ON f.borrower_id = b.borrower_id
    WHERE b.home_ownership IN ('RENT', 'OWN', 'MORTGAGE')
),
agg AS (
    SELECT home_ownership,
           AVG(is_def) AS default_rate,
           AVG(loan_amnt) AS avg_loan_amnt,
           COUNT(*) AS n_loans
    FROM joined
    GROUP BY home_ownership
)
SELECT home_ownership,
       default_rate,
       avg_loan_amnt,
       n_loans,
       RANK() OVER (ORDER BY default_rate DESC) AS default_rank
FROM agg
ORDER BY default_rate DESC;
