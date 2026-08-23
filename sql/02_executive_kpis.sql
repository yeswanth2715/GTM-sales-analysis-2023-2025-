WITH
period_revenue AS (
    SELECT SUM(recognized_revenue_inr) AS total_revenue_inr
    FROM revenue
    WHERE revenue_month BETWEEN '2023-01-01' AND '2025-12-01'
),
ending_base AS (
    SELECT
        SUM(closing_mrr_inr) AS ending_mrr_inr,
        COUNT(DISTINCT customer_id) AS ending_active_customers
    FROM revenue
    WHERE revenue_month = '2025-12-01'
),
starting_cohort AS (
    SELECT customer_id, closing_mrr_inr AS starting_mrr_inr
    FROM revenue
    WHERE revenue_month = '2024-12-01'
),
ending_cohort AS (
    SELECT customer_id, closing_mrr_inr AS ending_mrr_inr
    FROM revenue
    WHERE revenue_month = '2025-12-01'
),
retention AS (
    SELECT
        SUM(s.starting_mrr_inr) AS starting_mrr_inr,
        SUM(COALESCE(e.ending_mrr_inr, 0)) AS retained_ending_mrr_inr,
        SUM(MIN(s.starting_mrr_inr, COALESCE(e.ending_mrr_inr, 0))) AS gross_retained_mrr_inr
    FROM starting_cohort s
    LEFT JOIN ending_cohort e USING (customer_id)
),
new_business AS (
    SELECT
        COUNT(*) AS new_customers_2025,
        SUM(movement_mrr_inr) * 12 AS new_arr_2025_inr
    FROM revenue
    WHERE revenue_month BETWEEN '2025-01-01' AND '2025-12-01'
      AND revenue_type = 'New'
),
growth_events AS (
    SELECT
        SUM(CASE WHEN revenue_type = 'Expansion' THEN movement_mrr_inr ELSE 0 END) * 12 AS expansion_arr_2025_inr,
        SUM(CASE WHEN revenue_type = 'Upgrade' THEN movement_mrr_inr ELSE 0 END) * 12 AS upgrade_arr_2025_inr,
        SUM(CASE WHEN revenue_type = 'Reactivation' THEN movement_mrr_inr ELSE 0 END) * 12 AS reactivated_arr_2025_inr
    FROM revenue
    WHERE revenue_month BETWEEN '2025-01-01' AND '2025-12-01'
),
ending_2023 AS (
    SELECT SUM(closing_mrr_inr) AS mrr_inr
    FROM revenue WHERE revenue_month = '2023-12-01'
)
SELECT
    p.total_revenue_inr,
    e.ending_mrr_inr,
    e.ending_mrr_inr * 12 AS ending_arr_inr,
    e.ending_active_customers,
    n.new_customers_2025,
    n.new_arr_2025_inr,
    g.expansion_arr_2025_inr,
    g.upgrade_arr_2025_inr,
    g.reactivated_arr_2025_inr,
    ROUND(100.0 * r.retained_ending_mrr_inr / NULLIF(r.starting_mrr_inr, 0), 1) AS nrr_2025_pct,
    ROUND(100.0 * r.gross_retained_mrr_inr / NULLIF(r.starting_mrr_inr, 0), 1) AS grr_2025_pct,
    ROUND(100.0 * (e.ending_mrr_inr - y.mrr_inr) / NULLIF(y.mrr_inr, 0), 1) AS two_year_mrr_growth_pct
FROM period_revenue p
CROSS JOIN ending_base e
CROSS JOIN retention r
CROSS JOIN new_business n
CROSS JOIN growth_events g
CROSS JOIN ending_2023 y;
