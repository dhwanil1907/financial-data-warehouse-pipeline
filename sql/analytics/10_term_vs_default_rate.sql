-- Default rate: 36-month vs 60-month loans (dim_purpose.term).
WITH joined AS (
    SELECT p.term,
           CAST(f.is_default AS DOUBLE) AS is_def
    FROM fact_loans AS f
    INNER JOIN dim_purpose AS p ON f.purpose_id = p.purpose_id
    WHERE p.term IN ('36 months', '60 months')
)
SELECT term,
       AVG(is_def) AS default_rate,
       COUNT(*) AS n_loans
FROM joined
GROUP BY term
ORDER BY term;
