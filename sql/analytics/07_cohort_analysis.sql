-- Cohort default rates: early (2007–2010) vs later issue years (window for ordering).
WITH by_year AS (
    SELECT t.year,
           AVG(CAST(f.is_default AS DOUBLE)) AS cohort_default_rate
    FROM fact_loans AS f
    INNER JOIN dim_time AS t ON f.time_id = t.time_id
    GROUP BY t.year
),
tagged AS (
    SELECT year,
           cohort_default_rate,
           CASE
               WHEN year BETWEEN 2007 AND 2010 THEN 'early_2007_2010'
               ELSE 'later_2011_plus'
           END AS cohort_band,
           ROW_NUMBER() OVER (ORDER BY year) AS yr_seq
    FROM by_year
)
SELECT cohort_band,
       AVG(cohort_default_rate) AS avg_default_rate,
       MIN(year) AS min_year,
       MAX(year) AS max_year,
       COUNT(*) AS years_in_band
FROM tagged
GROUP BY cohort_band
ORDER BY cohort_band;
