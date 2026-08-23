# Methodology and reproducibility

## Decision frame

The project asks which revenue and GTM motions should be prioritized in a fictional B2B SaaS CRM business. The intended audience is a sales, customer-success, or growth leader who can act on channel mix, qualification, upgrades, adoption, and churn prevention.

## Scope

- Analysis window: January 2023 through December 2025
- Currency: INR, presented in crore where useful
- Customer population: Mid-Market and Large Enterprise only
- Products: Professional CRM and Enterprise CRM
- Evidence: deterministic synthetic data generated with seed `20260823`
- Database engine: SQLite

## Generation logic

The generator creates a 2022 opening cohort plus monthly new customers through 2025. Acquisition channels and plan tiers influence—but do not determine—modeled contract size, churn, expansion, upgrades, and reactivation. A fixed random seed makes every run reproducible.

Permanent churn stops revenue from the churn month forward and creates one row in `churn`. Reactivation represents a temporary billing suspension: the customer has no revenue rows during the gap, returns with a `Reactivation` event, and is deliberately excluded from `churn`.

## Metric calculations

### MRR and ARR

Monthly MRR is the sum of closing customer MRR for the month. ARR is MRR multiplied by 12. This is an operating run-rate, not signed annual contract value.

### Net revenue retention

For each calendar year, take customers active in the preceding December. Divide their MRR in the current December—including expansion, upgrades, reactivation, and churn effects—by their starting MRR. Exclude new customers from the cohort.

### Gross revenue retention

Use the same starting cohort, but cap each customer’s ending MRR at its starting MRR. This removes expansion and upgrade upside while retaining churn downside.

### Channel churn

Observed logo churn is permanent churned customers divided by all customers attributed to the channel in the modeled history. Because customer exposure periods differ, this is a descriptive portfolio ratio rather than an annualized rate.

## Analytical workflow

1. Generate four CSV tables and rebuild the SQLite database.
2. Enforce primary keys, foreign keys, uniqueness, check constraints, and indexes.
3. Run zero-tolerance data-quality checks.
4. Execute nine reviewed SQL analyses and export every result to CSV.
5. Build visuals only from exported query results.
6. Recompute headline metrics independently during validation.

## Caveats

The model is useful for demonstrating SQL, KPI design, and business reasoning. It does not estimate causal channel performance, and it lacks lead, opportunity, activity, quota, and spend tables required for funnel efficiency or CAC analysis.
