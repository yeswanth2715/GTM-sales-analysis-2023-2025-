WITH customer_portfolio AS (
    SELECT
        c.customer_id,
        c.company_segment,
        p.plan_tier AS starting_plan_tier,
        c.lifecycle_status,
        COALESCE(ch.mrr_lost_inr * 12, 0) AS permanent_churn_arr_lost_inr,
        COALESCE(SUM(CASE WHEN r.revenue_month = '2025-12-01' THEN r.arr_run_rate_inr ELSE 0 END), 0) AS ending_arr_inr
    FROM customers c
    JOIN products p ON p.product_id = c.initial_product_id
    LEFT JOIN churn ch ON ch.customer_id = c.customer_id
    LEFT JOIN revenue r ON r.customer_id = c.customer_id
    GROUP BY
        c.customer_id,
        c.company_segment,
        p.plan_tier,
        c.lifecycle_status,
        ch.mrr_lost_inr
)
SELECT
    company_segment,
    starting_plan_tier,
    COUNT(*) AS acquired_customers,
    SUM(CASE WHEN lifecycle_status = 'Churned' THEN 1 ELSE 0 END) AS permanently_churned_customers,
    ROUND(
        100.0 * SUM(CASE WHEN lifecycle_status = 'Churned' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    ) AS observed_logo_churn_pct,
    SUM(CASE WHEN ending_arr_inr > 0 THEN 1 ELSE 0 END) AS active_customers_dec_2025,
    SUM(ending_arr_inr) AS ending_arr_inr,
    SUM(permanent_churn_arr_lost_inr) AS permanent_churn_arr_lost_inr,
    ROUND(
        1.0 * SUM(ending_arr_inr)
        / NULLIF(SUM(CASE WHEN ending_arr_inr > 0 THEN 1 ELSE 0 END), 0),
        0
    ) AS avg_arr_per_active_customer_inr
FROM customer_portfolio
GROUP BY company_segment, starting_plan_tier
ORDER BY observed_logo_churn_pct DESC, ending_arr_inr DESC;
