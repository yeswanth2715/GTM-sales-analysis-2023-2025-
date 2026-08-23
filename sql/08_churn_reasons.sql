SELECT
    churn_reason,
    COUNT(*) AS churned_customers,
    SUM(mrr_lost_inr) AS mrr_lost_inr,
    SUM(mrr_lost_inr) * 12 AS arr_lost_inr,
    ROUND(AVG(tenure_months), 1) AS avg_tenure_months,
    ROUND(100.0 * SUM(mrr_lost_inr) / SUM(SUM(mrr_lost_inr)) OVER (), 1) AS lost_arr_mix_pct
FROM churn
WHERE churn_date BETWEEN '2023-01-01' AND '2025-12-31'
GROUP BY churn_reason
ORDER BY arr_lost_inr DESC;
