WITH owner_customers AS (
    SELECT
        c.sales_owner,
        c.customer_id,
        c.lifecycle_status,
        SUM(CASE WHEN r.revenue_month = '2025-12-01' THEN r.arr_run_rate_inr ELSE 0 END) AS ending_arr_inr,
        SUM(CASE WHEN r.revenue_type = 'New' AND r.revenue_month BETWEEN '2025-01-01' AND '2025-12-01' THEN r.movement_mrr_inr * 12 ELSE 0 END) AS new_arr_2025_inr,
        SUM(CASE WHEN r.revenue_type IN ('Expansion', 'Upgrade') AND r.revenue_month BETWEEN '2025-01-01' AND '2025-12-01' THEN r.movement_mrr_inr * 12 ELSE 0 END) AS expansion_upgrade_arr_2025_inr,
        SUM(CASE WHEN r.revenue_type = 'Upgrade' THEN 1 ELSE 0 END) AS upgrade_events
    FROM customers c
    LEFT JOIN revenue r ON r.customer_id = c.customer_id
    GROUP BY c.sales_owner, c.customer_id, c.lifecycle_status
)
SELECT
    sales_owner,
    COUNT(*) AS managed_customers,
    SUM(CASE WHEN ending_arr_inr > 0 THEN 1 ELSE 0 END) AS active_customers_dec_2025,
    SUM(ending_arr_inr) AS ending_arr_inr,
    SUM(new_arr_2025_inr) AS new_arr_2025_inr,
    SUM(expansion_upgrade_arr_2025_inr) AS expansion_upgrade_arr_2025_inr,
    SUM(upgrade_events) AS upgrade_events,
    ROUND(100.0 * SUM(CASE WHEN lifecycle_status = 'Churned' THEN 1 ELSE 0 END) / COUNT(*), 1) AS observed_logo_churn_pct
FROM owner_customers
GROUP BY sales_owner
ORDER BY ending_arr_inr DESC;
