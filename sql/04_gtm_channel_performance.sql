WITH customer_revenue AS (
    SELECT
        c.customer_id,
        c.acquisition_channel,
        c.first_contract_date,
        c.lifecycle_status,
        SUM(r.recognized_revenue_inr) AS recognized_revenue_inr,
        SUM(CASE WHEN r.revenue_month = '2025-12-01' THEN r.arr_run_rate_inr ELSE 0 END) AS ending_arr_inr,
        SUM(CASE WHEN r.revenue_month BETWEEN '2025-01-01' AND '2025-12-01' AND r.revenue_type = 'New' THEN r.movement_mrr_inr * 12 ELSE 0 END) AS new_arr_2025_inr,
        SUM(CASE WHEN r.revenue_month BETWEEN '2025-01-01' AND '2025-12-01' AND r.revenue_type = 'Expansion' THEN r.movement_mrr_inr * 12 ELSE 0 END) AS expansion_arr_2025_inr,
        SUM(CASE WHEN r.revenue_month BETWEEN '2025-01-01' AND '2025-12-01' AND r.revenue_type = 'Upgrade' THEN r.movement_mrr_inr * 12 ELSE 0 END) AS upgrade_arr_2025_inr,
        SUM(CASE WHEN r.revenue_month BETWEEN '2025-01-01' AND '2025-12-01' AND r.revenue_type = 'Reactivation' THEN r.movement_mrr_inr * 12 ELSE 0 END) AS reactivated_arr_2025_inr
    FROM customers c
    LEFT JOIN revenue r ON r.customer_id = c.customer_id
    GROUP BY c.customer_id, c.acquisition_channel, c.first_contract_date, c.lifecycle_status
)
SELECT
    acquisition_channel,
    COUNT(*) AS acquired_customers,
    SUM(CASE WHEN first_contract_date BETWEEN '2025-01-01' AND '2025-12-31' THEN 1 ELSE 0 END) AS new_customers_2025,
    SUM(CASE WHEN ending_arr_inr > 0 THEN 1 ELSE 0 END) AS active_customers_dec_2025,
    SUM(recognized_revenue_inr) AS recognized_revenue_36m_inr,
    SUM(ending_arr_inr) AS ending_arr_inr,
    SUM(new_arr_2025_inr) AS new_arr_2025_inr,
    SUM(expansion_arr_2025_inr) AS expansion_arr_2025_inr,
    SUM(upgrade_arr_2025_inr) AS upgrade_arr_2025_inr,
    SUM(reactivated_arr_2025_inr) AS reactivated_arr_2025_inr,
    SUM(CASE WHEN lifecycle_status = 'Churned' THEN 1 ELSE 0 END) AS permanently_churned_customers,
    ROUND(100.0 * SUM(CASE WHEN lifecycle_status = 'Churned' THEN 1 ELSE 0 END) / COUNT(*), 1) AS observed_logo_churn_pct,
    ROUND(1.0 * SUM(ending_arr_inr) / NULLIF(SUM(CASE WHEN ending_arr_inr > 0 THEN 1 ELSE 0 END), 0), 0) AS avg_arr_per_active_customer_inr
FROM customer_revenue
GROUP BY acquisition_channel
ORDER BY ending_arr_inr DESC;
