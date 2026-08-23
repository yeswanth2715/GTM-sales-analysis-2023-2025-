WITH years(year, start_month, end_month) AS (
    VALUES
        (2024, '2023-12-01', '2024-12-01'),
        (2025, '2024-12-01', '2025-12-01')
),
cohorts AS (
    SELECT
        y.year,
        s.customer_id,
        s.closing_mrr_inr AS starting_mrr_inr,
        COALESCE(e.closing_mrr_inr, 0) AS ending_mrr_inr
    FROM years y
    JOIN revenue s ON s.revenue_month = y.start_month
    LEFT JOIN revenue e
      ON e.customer_id = s.customer_id
     AND e.revenue_month = y.end_month
)
SELECT
    year,
    COUNT(*) AS starting_customers,
    SUM(CASE WHEN ending_mrr_inr > 0 THEN 1 ELSE 0 END) AS retained_customers,
    SUM(starting_mrr_inr) AS starting_mrr_inr,
    SUM(ending_mrr_inr) AS ending_mrr_same_cohort_inr,
    ROUND(100.0 * SUM(ending_mrr_inr) / NULLIF(SUM(starting_mrr_inr), 0), 1) AS nrr_pct,
    ROUND(100.0 * SUM(MIN(starting_mrr_inr, ending_mrr_inr)) / NULLIF(SUM(starting_mrr_inr), 0), 1) AS grr_pct,
    ROUND(100.0 * SUM(CASE WHEN ending_mrr_inr > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS logo_retention_pct
FROM cohorts
GROUP BY year
ORDER BY year;
