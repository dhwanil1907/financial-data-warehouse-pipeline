-- Default rate by DTI quartile (NTILE).
WITH scored AS (
    SELECT f.dti,
           CAST(f.is_default AS DOUBLE) AS is_def,
           NTILE(4) OVER (ORDER BY f.dti) AS dti_quartile
    FROM fact_loans AS f
    WHERE f.dti IS NOT NULL
)
SELECT dti_quartile,
       AVG(is_def) AS default_rate,
       AVG(dti) AS avg_dti,
       COUNT(*) AS n_loans
FROM scored
GROUP BY dti_quartile
ORDER BY dti_quartile;
