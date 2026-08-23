SELECT
    p.plan_tier,
    c.company_segment,
    COUNT(DISTINCT CASE WHEN r.revenue_month = '2025-12-01' THEN r.customer_id END) AS active_customers_dec_2025,
    SUM(r.recognized_revenue_inr) AS recognized_revenue_36m_inr,
    SUM(CASE WHEN r.revenue_month = '2025-12-01' THEN r.arr_run_rate_inr ELSE 0 END) AS ending_arr_inr,
    SUM(CASE WHEN r.revenue_type = 'New' AND r.revenue_month BETWEEN '2025-01-01' AND '2025-12-01' THEN r.movement_mrr_inr * 12 ELSE 0 END) AS new_arr_2025_inr,
    SUM(CASE WHEN r.revenue_type = 'Expansion' AND r.revenue_month BETWEEN '2025-01-01' AND '2025-12-01' THEN r.movement_mrr_inr * 12 ELSE 0 END) AS expansion_arr_2025_inr,
    SUM(CASE WHEN r.revenue_type = 'Upgrade' AND r.revenue_month BETWEEN '2025-01-01' AND '2025-12-01' THEN r.movement_mrr_inr * 12 ELSE 0 END) AS upgrade_arr_2025_inr,
    ROUND(
        100.0 * SUM(CASE WHEN r.revenue_month = '2025-12-01' THEN r.arr_run_rate_inr ELSE 0 END)
        / NULLIF(SUM(SUM(CASE WHEN r.revenue_month = '2025-12-01' THEN r.arr_run_rate_inr ELSE 0 END)) OVER (), 0),
        1
    ) AS ending_arr_mix_pct
FROM revenue r
JOIN products p ON p.product_id = r.product_id
JOIN customers c ON c.customer_id = r.customer_id
WHERE r.revenue_month BETWEEN '2023-01-01' AND '2025-12-01'
GROUP BY p.plan_tier, c.company_segment
ORDER BY ending_arr_inr DESC;
