WITH months AS (
    SELECT DISTINCT revenue_month
    FROM revenue
    WHERE revenue_month BETWEEN '2023-01-01' AND '2025-12-01'
),
monthly_revenue AS (
    SELECT
        revenue_month,
        COUNT(DISTINCT customer_id) AS active_customers,
        SUM(arr_run_rate_inr) AS ending_arr_inr,
        SUM(CASE WHEN revenue_type = 'New' THEN 1 ELSE 0 END) AS new_customers,
        SUM(CASE WHEN revenue_type = 'Reactivation' THEN 1 ELSE 0 END) AS reactivated_customers
    FROM revenue
    WHERE revenue_month BETWEEN '2023-01-01' AND '2025-12-01'
    GROUP BY revenue_month
),
monthly_churn AS (
    SELECT
        substr(churn_date, 1, 7) || '-01' AS revenue_month,
        COUNT(*) AS permanently_churned_customers,
        SUM(mrr_lost_inr) * 12 AS permanent_churn_arr_lost_inr
    FROM churn
    WHERE churn_date BETWEEN '2023-01-01' AND '2025-12-31'
    GROUP BY substr(churn_date, 1, 7) || '-01'
),
combined AS (
    SELECT
        m.revenue_month,
        r.active_customers,
        r.ending_arr_inr,
        r.new_customers,
        r.reactivated_customers,
        COALESCE(c.permanently_churned_customers, 0) AS permanently_churned_customers,
        COALESCE(c.permanent_churn_arr_lost_inr, 0) AS permanent_churn_arr_lost_inr
    FROM months m
    JOIN monthly_revenue r USING (revenue_month)
    LEFT JOIN monthly_churn c USING (revenue_month)
),
with_comparisons AS (
    SELECT
        *,
        LAG(active_customers) OVER (ORDER BY revenue_month) AS prior_month_active_customers,
        LAG(ending_arr_inr) OVER (ORDER BY revenue_month) AS prior_month_arr_inr,
        LAG(active_customers, 12) OVER (ORDER BY revenue_month) AS prior_year_active_customers,
        LAG(ending_arr_inr, 12) OVER (ORDER BY revenue_month) AS prior_year_arr_inr
    FROM combined
)
SELECT
    revenue_month,
    active_customers,
    new_customers,
    reactivated_customers,
    permanently_churned_customers,
    new_customers - permanently_churned_customers AS net_new_minus_permanent_churn,
    active_customers - prior_month_active_customers AS net_active_customer_change,
    ending_arr_inr,
    ROUND(1.0 * ending_arr_inr / NULLIF(active_customers, 0), 0) AS avg_arr_per_active_customer_inr,
    permanent_churn_arr_lost_inr,
    ROUND(100.0 * (ending_arr_inr - prior_year_arr_inr) / NULLIF(prior_year_arr_inr, 0), 1) AS yoy_arr_growth_pct,
    ROUND(100.0 * (active_customers - prior_year_active_customers) / NULLIF(prior_year_active_customers, 0), 1) AS yoy_active_customer_growth_pct
FROM with_comparisons
ORDER BY revenue_month;
