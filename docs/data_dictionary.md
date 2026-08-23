# Data dictionary

All data is synthetic. Dates use ISO `YYYY-MM-DD`; money is stored as whole INR.

## `customers`

Grain: one row per customer account.

| Column | Type | Description |
|---|---|---|
| `customer_id` | TEXT | Primary key. |
| `company_name` | TEXT | Fictional company name. |
| `industry` | TEXT | Modeled customer industry. |
| `company_segment` | TEXT | `Mid-Market` or `Large Enterprise`; no SMB records. |
| `region` | TEXT | North, South, West, East, or Central. |
| `acquisition_channel` | TEXT | Partner, Outbound, Inbound, Events, or Referral. |
| `sales_owner` | TEXT | Fictional account owner. |
| `signup_date` | DATE | Modeled signup date. |
| `first_contract_date` | DATE | First paid contract month/date. |
| `initial_product_id` | TEXT | Foreign key to the original product. |
| `current_product_id` | TEXT | Foreign key to the plan held at the end of the modeled period. |
| `lifecycle_status` | TEXT | `Active` or permanently `Churned` as of December 2025. |

## `products`

Grain: one row per CRM plan.

| Column | Type | Description |
|---|---|---|
| `product_id` | TEXT | Primary key. |
| `product_name` | TEXT | Fictional product name. |
| `plan_tier` | TEXT | Professional or Enterprise. |
| `billing_frequency` | TEXT | Annual contract cadence. |
| `included_users` | INTEGER | Modeled included-user allowance. |
| `base_monthly_price_inr` | INTEGER | Modeled base monthly price in INR. |
| `target_segment` | TEXT | Primary target customer segment. |

## `revenue`

Grain: one row per active customer per month. A customer-month is unique.

| Column | Type | Description |
|---|---|---|
| `revenue_id` | TEXT | Primary key. |
| `revenue_month` | DATE | First day of the recognized revenue month. |
| `customer_id` | TEXT | Foreign key to `customers`. |
| `product_id` | TEXT | Product held during that month. |
| `revenue_type` | TEXT | `New`, `Recurring`, `Expansion`, `Upgrade`, or `Reactivation`. |
| `opening_mrr_inr` | INTEGER | Customer MRR before the month’s movement. |
| `movement_mrr_inr` | INTEGER | Positive MRR added by the month’s event; zero for recurring months. |
| `closing_mrr_inr` | INTEGER | Customer MRR at month end. |
| `recognized_revenue_inr` | INTEGER | Monthly recognized subscription revenue. |
| `arr_run_rate_inr` | INTEGER | `closing_mrr_inr × 12`. |

`revenue_type` is the primary event for that customer-month. Upgrade changes `product_id` from Professional to Enterprise. Reactivated customers have a gap with no revenue rows, then return with `Reactivation`.

## `churn`

Grain: one row per permanently churned customer. Reactivated customers are excluded.

| Column | Type | Description |
|---|---|---|
| `churn_id` | TEXT | Primary key. |
| `customer_id` | TEXT | Unique foreign key to `customers`. |
| `product_id` | TEXT | Product held immediately before churn. |
| `churn_date` | DATE | Permanent churn date. |
| `churn_reason` | TEXT | Modeled primary reason for churn. |
| `mrr_lost_inr` | INTEGER | MRR lost at permanent churn. |
| `tenure_months` | INTEGER | Paid tenure before permanent churn. |
