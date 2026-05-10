-- Month-over-month loan count and funded volume (LAG window).
WITH monthly AS (
    SELECT t.year,
           t.month,
           COUNT(*) AS loan_cnt,
           SUM(f.funded_amnt) AS funded_vol
    FROM fact_loans AS f
    INNER JOIN dim_time AS t ON f.time_id = t.time_id
    GROUP BY t.year,
             t.month
),
mom AS (
    SELECT year,
           month,
           loan_cnt,
           funded_vol,
           LAG(loan_cnt) OVER (ORDER BY year, month) AS prev_loan_cnt,
           LAG(funded_vol) OVER (ORDER BY year, month) AS prev_funded_vol
    FROM monthly
)
SELECT year,
       month,
       loan_cnt,
       funded_vol,
       prev_loan_cnt,
       prev_funded_vol,
       loan_cnt - prev_loan_cnt AS mom_loan_delta,
       funded_vol - prev_funded_vol AS mom_funded_delta
FROM mom
ORDER BY year,
         month;
