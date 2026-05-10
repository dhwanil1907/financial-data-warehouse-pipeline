-- Average interest rate (decimal, e.g. 0.12 = 12%) and loan size by state; min 500 loans.
-- int_rate in warehouse is decimal (not percent points).
WITH by_state AS (
    SELECT b.addr_state,
           AVG(f.int_rate) AS avg_int_rate,
           AVG(f.loan_amnt) AS avg_loan_amnt,
           COUNT(*) AS n_loans
    FROM fact_loans AS f
    INNER JOIN dim_borrower AS b ON f.borrower_id = b.borrower_id
    GROUP BY b.addr_state
    HAVING COUNT(*) >= 500
)
SELECT addr_state,
       avg_int_rate,
       avg_loan_amnt,
       n_loans,
       RANK() OVER (ORDER BY avg_int_rate DESC) AS rate_rank
FROM by_state
ORDER BY avg_int_rate DESC;
