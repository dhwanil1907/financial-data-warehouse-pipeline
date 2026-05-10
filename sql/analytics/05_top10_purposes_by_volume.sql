-- Top 10 purposes by total funded amount (RANK window).
WITH by_purpose AS (
    SELECT p.purpose,
           SUM(f.funded_amnt) AS total_funded
    FROM fact_loans AS f
    INNER JOIN dim_purpose AS p ON f.purpose_id = p.purpose_id
    GROUP BY p.purpose
),
ranked AS (
    SELECT purpose,
           total_funded,
           RANK() OVER (ORDER BY total_funded DESC) AS vol_rank
    FROM by_purpose
)
SELECT purpose,
       total_funded,
       vol_rank
FROM ranked
WHERE vol_rank <= 10
ORDER BY vol_rank;
