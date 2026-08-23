# Validation report

## Overall assessment: Ready to share

The dataset, SQL calculations, exported results, report package, and static visuals were validated before publication. All source records are deterministic synthetic data through December 2025.

## Methodology review

The analysis answers a revenue-growth and GTM prioritization question at customer-month grain. KPI populations, dates, INR units, cohort denominators, and exclusions are stated in the README and methodology. Channel comparisons are descriptive; no causal claims are made.

## Calculation and data-quality checks

| Check | Result | Evidence |
|---|---|---|
| Core SQL data-quality checks | Passed | 9 checks; failures: none |
| Expected table volumes | Passed | Expected and actual: {'customers': 529, 'products': 2, 'revenue': 10453, 'churn': 40} |
| Complete 36-month coverage | Passed | 2023-01-01 to 2025-12-01; 36 months |
| Required-field completeness | Passed | Nulls across NOT NULL columns: 0 |
| Financial-domain validity | Passed | Invalid non-positive/negative money rows: 0 |
| Controlled-value validity | Passed | Rows outside allowed enums: 0 |
| Referential integrity | Passed | Foreign-key failures: 0 |
| Reactivation/churn business rule | Passed | Reactivated customers in permanent churn: 0 |
| Ending ARR independently reconciled | Passed | KPI=1,509,240,000; MRR×12=1,509,240,000; direct ARR sum=1,509,240,000 |
| 2025 NRR/GRR independently recomputed | Passed | NRR=100.7%; GRR=94.4% |
| Channel subtotals reconcile | Passed | Channel sum=1,509,240,000; headline=1,509,240,000 |
| Plan/segment subtotals reconcile | Passed | Plan/segment base=1,509,240,000; headline=1,509,240,000 |
| 2025 post-sale growth reconciled | Passed | Event sum=120,000,000; KPI components=120,000,000 |
| Deterministic regeneration | Passed | Matching CSV hashes: {'customers.csv': True, 'products.csv': True, 'revenue.csv': True, 'churn.csv': True} |
| Canonical report artifact is bounded | Passed | Datasets: {'kpis': 1, 'monthly_growth': 36, 'channel_performance': 5, 'growth_events_2025': 4, 'churn_reasons': 5} |
| Portable report package exists | Passed | report.html size: 462,942 bytes |
| README headline claims match reviewed outputs | Passed | Missing expected claims: none |
| Final visual exports have intended dimensions | Passed | Dimensions: {'dashboard_preview.png': (1600, 1170), 'linkedin_project_summary.png': (1200, 1420)} |

## Visualization review

The dashboard and LinkedIn visual use line and bar charts appropriate to 36-month trends and ranked categorical comparisons. Bar charts start at zero, the trend uses 36 observed points, INR crore is labeled, and the final 1600×1170 and 1200×1420 PNG exports were visually inspected for clipping and legibility.

## Required caveats for readers

- The evidence is synthetic and demonstrates an analytical workflow rather than a real company result.
- ARR is a monthly recurring-revenue run-rate, not audited revenue or signed contract value.
- Channel churn is an observed portfolio ratio with unequal exposure time, not an annualized churn rate.
- Funnel conversion, CAC, payback, quota attainment, and sales cycle are unavailable in the four-table scope.
- Portable report verification was structural because no compatible Chromium executable was installed; the canonical artifact itself passed schema validation and the semantic report remains self-contained.

## Incomplete handoff blockers

None for the repository package. The optional live Sites publication encountered a service interruption, so the validated self-contained `report/report.html` is the durable report artifact.
