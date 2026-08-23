WITH monthly AS (
    SELECT
        revenue_month,
        SUM(recognized_revenue_inr) AS recognized_revenue_inr,
        SUM(closing_mrr_inr) AS ending_mrr_inr,
        SUM(arr_run_rate_inr) AS ending_arr_inr,
        COUNT(DISTINCT customer_id) AS active_customers,
        SUM(CASE WHEN revenue_type = 'New' THEN 1 ELSE 0 END) AS new_customers,
        SUM(CASE WHEN revenue_type = 'Expansion' THEN movement_mrr_inr ELSE 0 END) AS expansion_mrr_inr,
        SUM(CASE WHEN revenue_type = 'Upgrade' THEN movement_mrr_inr ELSE 0 END) AS upgrade_mrr_inr,
        SUM(CASE WHEN revenue_type = 'Reactivation' THEN movement_mrr_inr ELSE 0 END) AS reactivated_mrr_inr
    FROM revenue
    WHERE revenue_month BETWEEN '2023-01-01' AND '2025-12-01'
    GROUP BY revenue_month
)
SELECT
    revenue_month,
    recognized_revenue_inr,
    ending_mrr_inr,
    ending_arr_inr,
    active_customers,
    new_customers,
    expansion_mrr_inr,
    upgrade_mrr_inr,
    reactivated_mrr_inr,
    ROUND(
        100.0 * (ending_mrr_inr - LAG(ending_mrr_inr, 12) OVER (ORDER BY revenue_month))
        / NULLIF(LAG(ending_mrr_inr, 12) OVER (ORDER BY revenue_month), 0),
        1
    ) AS yoy_mrr_growth_pct
FROM monthly
ORDER BY revenue_month;
