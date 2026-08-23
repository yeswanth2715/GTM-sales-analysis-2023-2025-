-- Every check should return zero issues.
SELECT 'duplicate_customer_id' AS check_name,
       COUNT(*) - COUNT(DISTINCT customer_id) AS issue_count
FROM customers
UNION ALL
SELECT 'duplicate_customer_month',
       COUNT(*) - COUNT(DISTINCT revenue_month || '|' || customer_id)
FROM revenue
UNION ALL
SELECT 'orphan_revenue_customer', COUNT(*)
FROM revenue r LEFT JOIN customers c ON c.customer_id = r.customer_id
WHERE c.customer_id IS NULL
UNION ALL
SELECT 'orphan_revenue_product', COUNT(*)
FROM revenue r LEFT JOIN products p ON p.product_id = r.product_id
WHERE p.product_id IS NULL
UNION ALL
SELECT 'orphan_churn_customer', COUNT(*)
FROM churn ch LEFT JOIN customers c ON c.customer_id = ch.customer_id
WHERE c.customer_id IS NULL
UNION ALL
SELECT 'invalid_arr_math', COUNT(*)
FROM revenue
WHERE arr_run_rate_inr <> closing_mrr_inr * 12
UNION ALL
SELECT 'reactivated_customer_in_churn', COUNT(*)
FROM churn ch
JOIN revenue r ON r.customer_id = ch.customer_id
WHERE r.revenue_type = 'Reactivation'
UNION ALL
SELECT 'churn_status_mismatch', COUNT(*)
FROM churn ch
JOIN customers c ON c.customer_id = ch.customer_id
WHERE c.lifecycle_status <> 'Churned'
UNION ALL
SELECT 'smb_records', COUNT(*)
FROM customers
WHERE company_segment = 'SMB';
