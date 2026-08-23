# Chart map

This file records the visualization choices used in the portfolio preview and report.

| Report segment | Analytical question | Family / type | Fields | Supported takeaway | Palette policy |
|---|---|---|---|---|---|
| Revenue trajectory | How did the recurring-revenue run-rate change? | Trend / single-series line | `revenue_month`, `ending_arr_inr` | ARR rose consistently across 36 observed months. | Single-root blue |
| Growth quality | Is ARR growth keeping pace with customer growth, and is momentum decelerating? | Trend / highlighted two-series line | `revenue_month`, `yoy_arr_growth_pct`, `yoy_active_customer_growth_pct` | Both rates remain positive but slow materially through 2025; ARR grows faster than the customer base. | Hard two-root blue and gold |
| Customer flow | Are customer additions exceeding permanent churn? | Trend / two-series line | `revenue_month`, new customers, permanent churn | New additions remain above permanent churn in every observed month. | Hard two-root blue and pink |
| Segment churn | Which customer segment has the higher observed permanent logo-churn rate? | Comparison / vertical bar | `company_segment`, `observed_logo_churn_pct` | Mid-Market has higher logo churn, while Enterprise losses carry more ARR per account. | Single-root pink |
| GTM channel quality | Which acquisition channels contribute the most ending ARR? | Comparison / sorted horizontal bar | `acquisition_channel`, `ending_arr_inr` | Partner leads ending ARR; Outbound is close but carries higher churn. | Relaxed multi-category |
| Growth engines | What added ARR during 2025? | Comparison / categorical bar | movement type, `added_arr_inr` | New business is the largest engine; post-sale motions contribute meaningful incremental ARR. | Relaxed multi-category |
| Churn drivers | Which permanent-churn reasons destroyed the most ARR? | Ranking / horizontal bar | `churn_reason`, `arr_lost_inr` | Missing integrations and low adoption are the largest modeled churn drivers. | Single-root pink |

All magnitude bars start at zero. Trend views use 24 or 36 observed monthly points. Growth rates use common percent scales, customer-flow series use customer counts, and monetary values are shown in INR crore. Static SVG and PNG exports were inspected at their final dimensions.
