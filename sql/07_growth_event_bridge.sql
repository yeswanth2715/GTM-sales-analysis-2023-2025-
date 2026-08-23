SELECT
    CAST(substr(revenue_month, 1, 4) AS INTEGER) AS year,
    revenue_type,
    COUNT(*) AS event_count,
    SUM(movement_mrr_inr) AS added_mrr_inr,
    SUM(movement_mrr_inr) * 12 AS added_arr_inr
FROM revenue
WHERE revenue_type IN ('New', 'Expansion', 'Upgrade', 'Reactivation')
  AND revenue_month BETWEEN '2023-01-01' AND '2025-12-01'
GROUP BY CAST(substr(revenue_month, 1, 4) AS INTEGER), revenue_type
ORDER BY year, CASE revenue_type
    WHEN 'New' THEN 1
    WHEN 'Expansion' THEN 2
    WHEN 'Upgrade' THEN 3
    WHEN 'Reactivation' THEN 4
END;
