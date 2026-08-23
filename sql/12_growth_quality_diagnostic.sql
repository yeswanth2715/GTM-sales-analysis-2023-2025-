WITH year_end AS (
    SELECT
        CAST(substr(revenue_month, 1, 4) AS INTEGER) AS year,
        SUM(arr_run_rate_inr) AS ending_arr_inr,
        COUNT(DISTINCT customer_id) AS active_customers,
        ROUND(1.0 * SUM(arr_run_rate_inr) / COUNT(DISTINCT customer_id), 0) AS avg_arr_per_active_customer_inr
    FROM revenue
    WHERE substr(revenue_month, 6, 5) = '12-01'
      AND revenue_month BETWEEN '2023-01-01' AND '2025-12-01'
    GROUP BY CAST(substr(revenue_month, 1, 4) AS INTEGER)
),
annual_new_and_post_sale AS (
    SELECT
        CAST(substr(revenue_month, 1, 4) AS INTEGER) AS year,
        SUM(CASE WHEN revenue_type = 'New' THEN 1 ELSE 0 END) AS new_customers,
        SUM(
            CASE WHEN revenue_type IN ('Expansion', 'Upgrade', 'Reactivation')
                 THEN movement_mrr_inr * 12 ELSE 0 END
        ) AS post_sale_added_arr_inr
    FROM revenue
    WHERE revenue_month BETWEEN '2023-01-01' AND '2025-12-01'
    GROUP BY CAST(substr(revenue_month, 1, 4) AS INTEGER)
),
annual_churn AS (
    SELECT
        CAST(substr(churn_date, 1, 4) AS INTEGER) AS year,
        COUNT(*) AS permanently_churned_customers,
        SUM(mrr_lost_inr) * 12 AS permanent_churn_arr_lost_inr
    FROM churn
    WHERE churn_date BETWEEN '2023-01-01' AND '2025-12-31'
    GROUP BY CAST(substr(churn_date, 1, 4) AS INTEGER)
),
annual AS (
    SELECT
        y.year,
        y.ending_arr_inr,
        y.active_customers,
        y.avg_arr_per_active_customer_inr,
        n.new_customers,
        COALESCE(c.permanently_churned_customers, 0) AS permanently_churned_customers,
        n.new_customers - COALESCE(c.permanently_churned_customers, 0) AS net_new_minus_permanent_churn,
        n.post_sale_added_arr_inr,
        COALESCE(c.permanent_churn_arr_lost_inr, 0) AS permanent_churn_arr_lost_inr,
        LAG(y.ending_arr_inr) OVER (ORDER BY y.year) AS prior_year_arr_inr,
        LAG(y.active_customers) OVER (ORDER BY y.year) AS prior_year_active_customers,
        LAG(y.avg_arr_per_active_customer_inr) OVER (ORDER BY y.year) AS prior_year_avg_arr_inr
    FROM year_end y
    JOIN annual_new_and_post_sale n USING (year)
    LEFT JOIN annual_churn c USING (year)
)
SELECT
    year,
    ending_arr_inr,
    active_customers,
    avg_arr_per_active_customer_inr,
    new_customers,
    permanently_churned_customers,
    net_new_minus_permanent_churn,
    post_sale_added_arr_inr,
    permanent_churn_arr_lost_inr,
    ROUND(100.0 * (ending_arr_inr - prior_year_arr_inr) / NULLIF(prior_year_arr_inr, 0), 1) AS yoy_arr_growth_pct,
    ROUND(100.0 * (active_customers - prior_year_active_customers) / NULLIF(prior_year_active_customers, 0), 1) AS yoy_active_customer_growth_pct,
    ROUND(
        100.0 * (avg_arr_per_active_customer_inr - prior_year_avg_arr_inr)
        / NULLIF(prior_year_avg_arr_inr, 0),
        1
    ) AS yoy_avg_arr_per_customer_growth_pct,
    ROUND(
        100.0 * (ending_arr_inr - prior_year_arr_inr) / NULLIF(prior_year_arr_inr, 0)
        - 100.0 * (active_customers - prior_year_active_customers) / NULLIF(prior_year_active_customers, 0),
        1
    ) AS arr_growth_minus_customer_growth_pp
FROM annual
ORDER BY year;
