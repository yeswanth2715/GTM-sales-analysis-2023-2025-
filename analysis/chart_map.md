# Chart map

This file records the visualization choices used in the portfolio preview and report.

| Report segment | Analytical question | Family / type | Fields | Supported takeaway | Palette policy |
|---|---|---|---|---|---|
| Revenue trajectory | How did the recurring-revenue run-rate change? | Trend / single-series line | `revenue_month`, `ending_arr_inr` | ARR rose consistently across 36 observed months. | Single-root blue |
| GTM channel quality | Which acquisition channels contribute the most ending ARR? | Comparison / sorted horizontal bar | `acquisition_channel`, `ending_arr_inr` | Partner leads ending ARR; Outbound is close but carries higher churn. | Relaxed multi-category |
| Growth engines | What added ARR during 2025? | Comparison / categorical bar | movement type, `added_arr_inr` | New business is the largest engine; post-sale motions contribute meaningful incremental ARR. | Relaxed multi-category |
| Churn drivers | Which permanent-churn reasons destroyed the most ARR? | Ranking / horizontal bar | `churn_reason`, `arr_lost_inr` | Missing integrations and low adoption are the largest modeled churn drivers. | Single-root pink |

All bars start at zero. The trend uses 36 observed monthly points. Values are shown in INR crore. Static SVG and PNG exports were inspected at their final dimensions.
