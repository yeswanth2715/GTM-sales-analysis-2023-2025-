#!/usr/bin/env python3
"""Build the canonical Data Analytics report artifact used for Sites publishing."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "analysis" / "outputs"
REPORT = ROOT / "report"
GENERATED_AT = "2026-08-23T16:30:00Z"


def csv_rows(name: str) -> list[dict]:
    with (OUTPUTS / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def as_number(value: str | int | float | None):
    if value in (None, ""):
        return None
    text = str(value)
    return float(text) if "." in text else int(text)


def read_sql(name: str) -> str:
    return (ROOT / "sql" / name).read_text(encoding="utf-8")


def source(source_id: str, label: str, sql_file: str, description: str, tables: list[str], filters: list[str], definitions: dict[str, str]) -> dict:
    return {
        "id": source_id,
        "label": label,
        "path": f"sql/{sql_file}",
        "query": {
            "language": "sql",
            "engine": "SQLite",
            "sql": read_sql(sql_file),
            "description": description,
            "tables_used": tables,
            "filters": filters,
            "metric_definitions": definitions,
            "executed_at": GENERATED_AT,
        },
    }


def main() -> None:
    metrics = json.loads((OUTPUTS / "headline_metrics.json").read_text(encoding="utf-8"))
    monthly_raw = csv_rows("03_monthly_revenue_growth.csv")
    channel_raw = csv_rows("04_gtm_channel_performance.csv")
    growth_raw = csv_rows("07_growth_event_bridge.csv")
    churn_raw = csv_rows("08_churn_reasons.csv")

    kpis = [{
        "ending_arr_crore": round(metrics["ending_arr_inr"] / 10_000_000, 1),
        "ending_active_customers": metrics["ending_active_customers"],
        "nrr_2025_rate": metrics["nrr_2025_pct"] / 100,
        "grr_2025_rate": metrics["grr_2025_pct"] / 100,
        "two_year_mrr_growth_rate": metrics["two_year_mrr_growth_pct"] / 100,
    }]
    monthly = []
    for row in monthly_raw:
        monthly.append({
            "revenue_month": row["revenue_month"],
            "ending_arr_crore": round(as_number(row["ending_arr_inr"]) / 10_000_000, 2),
            "ending_mrr_crore": round(as_number(row["ending_mrr_inr"]) / 10_000_000, 2),
            "active_customers": as_number(row["active_customers"]),
            "new_customers": as_number(row["new_customers"]),
            "yoy_mrr_growth_rate": None if row["yoy_mrr_growth_pct"] == "" else as_number(row["yoy_mrr_growth_pct"]) / 100,
        })
    channels = []
    for rank, row in enumerate(channel_raw, start=1):
        channels.append({
            "rank": rank,
            "acquisition_channel": row["acquisition_channel"],
            "ending_arr_crore": round(as_number(row["ending_arr_inr"]) / 10_000_000, 2),
            "new_arr_2025_crore": round(as_number(row["new_arr_2025_inr"]) / 10_000_000, 2),
            "active_customers_dec_2025": as_number(row["active_customers_dec_2025"]),
            "observed_logo_churn_rate": as_number(row["observed_logo_churn_pct"]) / 100,
            "avg_arr_per_active_customer_crore": round(as_number(row["avg_arr_per_active_customer_inr"]) / 10_000_000, 3),
        })
    growth = []
    for row in growth_raw:
        if row["year"] == "2025":
            growth.append({
                "revenue_type": row["revenue_type"],
                "event_count": as_number(row["event_count"]),
                "added_arr_crore": round(as_number(row["added_arr_inr"]) / 10_000_000, 2),
                "added_mrr_crore": round(as_number(row["added_mrr_inr"]) / 10_000_000, 2),
            })
    churn = []
    for row in churn_raw:
        churn.append({
            "churn_reason": row["churn_reason"],
            "churned_customers": as_number(row["churned_customers"]),
            "arr_lost_crore": round(as_number(row["arr_lost_inr"]) / 10_000_000, 2),
            "lost_arr_mix_rate": as_number(row["lost_arr_mix_pct"]) / 100,
            "avg_tenure_months": as_number(row["avg_tenure_months"]),
        })

    sources = [
        source(
            "src_kpis", "Executive KPI query", "02_executive_kpis.sql",
            "Calculates ending recurring-revenue scale, new and post-sale growth, and 2025 cohort retention.",
            ["customers", "revenue"],
            ["Revenue months from 2023-01-01 through 2025-12-01", "2025 retention cohort starts in December 2024"],
            {
                "Ending ARR": "Sum December 2025 closing MRR and multiply by 12.",
                "NRR": "December 2025 MRR for the December 2024 starting cohort divided by that cohort's starting MRR; new customers excluded.",
                "GRR": "Same cohort, with each customer's ending MRR capped at starting MRR.",
            },
        ),
        source(
            "src_monthly", "Monthly revenue growth query", "03_monthly_revenue_growth.sql",
            "Aggregates monthly MRR, ARR, customer volume, and growth movements across 36 months.",
            ["revenue"],
            ["Revenue months from 2023-01-01 through 2025-12-01"],
            {"Ending ARR": "Sum customer closing MRR by month and multiply by 12."},
        ),
        source(
            "src_channels", "GTM channel performance query", "04_gtm_channel_performance.sql",
            "Compares acquisition channels on ending ARR, customer volume, new ARR, post-sale growth, and permanent churn.",
            ["customers", "revenue"],
            ["Ending ARR is measured at 2025-12-01", "Permanent churn is observed over the full modeled history"],
            {"Observed logo churn": "Permanently churned customers divided by all customers attributed to the channel; not annualized."},
        ),
        source(
            "src_growth", "Growth event bridge query", "07_growth_event_bridge.sql",
            "Summarizes ARR added by new business, expansion, upgrades, and reactivation.",
            ["revenue"],
            ["Events from 2023-01-01 through 2025-12-01", "Chart uses 2025 events"],
            {"Added ARR": "Positive event MRR movement multiplied by 12."},
        ),
        source(
            "src_churn", "Permanent churn reason query", "08_churn_reasons.sql",
            "Ranks permanent churn reasons by lost recurring-revenue run-rate.",
            ["churn"],
            ["Churn dates from 2023-01-01 through 2025-12-31", "Reactivated customers excluded"],
            {"ARR lost": "MRR lost at permanent churn multiplied by 12."},
        ),
    ]

    title = "B2B SaaS Revenue Growth & GTM Performance"
    manifest = {
        "version": 1,
        "surface": "report",
        "title": title,
        "description": "A decision-ready analysis of recurring-revenue growth, acquisition-channel quality, post-sale expansion, and permanent churn in a fictional B2B SaaS CRM.",
        "generatedAt": GENERATED_AT,
        "sources": sources,
        "cards": [
            {
                "id": "card_ending_arr",
                "description": "December 2025 recurring-revenue run-rate.",
                "dataset": "kpis",
                "sourceId": "src_kpis",
                "metrics": [
                    {"label": "Ending ARR", "field": "ending_arr_crore", "format": "number", "unit": "₹ crore"},
                    {"label": "Two-year MRR growth", "field": "two_year_mrr_growth_rate", "format": "percent", "signed": True},
                ],
            },
            {
                "id": "card_active_customers",
                "description": "Professional and Enterprise customers with December 2025 revenue.",
                "dataset": "kpis",
                "sourceId": "src_kpis",
                "metrics": [
                    {"label": "Active customers", "field": "ending_active_customers", "format": "number"},
                ],
            },
            {
                "id": "card_nrr",
                "description": "Retention for customers active in December 2024; new customers excluded.",
                "dataset": "kpis",
                "sourceId": "src_kpis",
                "metrics": [
                    {"label": "NRR", "field": "nrr_2025_rate", "format": "percent"},
                    {"label": "GRR", "field": "grr_2025_rate", "format": "percent"},
                ],
            },
        ],
        "charts": [
            {
                "id": "chart_monthly_arr",
                "title": "Monthly ending ARR",
                "description": "Thirty-six observed months, values in INR crore.",
                "type": "line",
                "dataset": "monthly_growth",
                "sourceId": "src_monthly",
                "encodings": {
                    "x": {"field": "revenue_month", "type": "temporal", "title": "Month"},
                    "y": {"field": "ending_arr_crore", "type": "quantitative", "title": "Ending ARR (₹ crore)"},
                },
                "options": {"legend": {"show": False}, "palette": {"kind": "single", "colors": ["#2563EB"]}},
            },
            {
                "id": "chart_channels",
                "title": "Ending ARR by acquisition channel",
                "description": "December 2025 run-rate, values in INR crore.",
                "type": "bar",
                "dataset": "channel_performance",
                "sourceId": "src_channels",
                "encodings": {
                    "x": {"field": "acquisition_channel", "type": "nominal", "title": "Acquisition channel"},
                    "y": {"field": "ending_arr_crore", "type": "quantitative", "title": "Ending ARR (₹ crore)"},
                },
                "options": {"orientation": "horizontal", "grouping": "grouped", "legend": {"show": False}},
            },
            {
                "id": "chart_growth_engines",
                "title": "2025 ARR added by growth motion",
                "description": "New business and positive post-sale movements, values in INR crore.",
                "type": "bar",
                "dataset": "growth_events_2025",
                "sourceId": "src_growth",
                "encodings": {
                    "x": {"field": "revenue_type", "type": "nominal", "title": "Growth motion"},
                    "y": {"field": "added_arr_crore", "type": "quantitative", "title": "Added ARR (₹ crore)"},
                },
                "options": {"orientation": "vertical", "grouping": "grouped", "legend": {"show": False}},
            },
            {
                "id": "chart_churn_reasons",
                "title": "Permanent churn by reason",
                "description": "ARR lost during 2023–2025, values in INR crore.",
                "type": "bar",
                "dataset": "churn_reasons",
                "sourceId": "src_churn",
                "encodings": {
                    "x": {"field": "churn_reason", "type": "nominal", "title": "Churn reason"},
                    "y": {"field": "arr_lost_crore", "type": "quantitative", "title": "ARR lost (₹ crore)"},
                },
                "options": {"orientation": "horizontal", "grouping": "grouped", "legend": {"show": False}},
            },
        ],
        "tables": [
            {
                "id": "table_channels",
                "title": "Acquisition channel detail",
                "description": "Ending scale, 2025 new business, active customers, and observed permanent churn.",
                "dataset": "channel_performance",
                "sourceId": "src_channels",
                "columns": [
                    {"field": "rank", "label": "Rank", "format": "number"},
                    {"field": "acquisition_channel", "label": "Channel"},
                    {"field": "ending_arr_crore", "label": "Ending ARR", "format": "number", "unit": "₹ crore"},
                    {"field": "new_arr_2025_crore", "label": "2025 new ARR", "format": "number", "unit": "₹ crore"},
                    {"field": "active_customers_dec_2025", "label": "Active customers", "format": "number"},
                    {"field": "observed_logo_churn_rate", "label": "Observed logo churn", "format": "percent"},
                ],
                "defaultSort": {"field": "ending_arr_crore", "direction": "desc"},
            }
        ],
        "blocks": [
            {"id": "title", "type": "markdown", "body": f"# {title}"},
            {
                "id": "executive_summary",
                "type": "markdown",
                "sourceId": "src_kpis",
                "body": "## Executive Summary\n\n- **Recurring revenue grew strongly.** Ending ARR reached ₹150.9 crore in December 2025, 152.6% above the December 2023 MRR run-rate.\n- **Retention is healthy but must be read with gross losses.** The 2025 starting cohort ended at 100.7% NRR and 94.4% GRR.\n- **Post-sale motions matter.** Expansion, upgrades, and reactivation added ₹12.0 crore of ARR during 2025.\n- **GTM quality is uneven.** Partner leads ending ARR, while Outbound reached similar scale with materially higher observed churn.",
            },
            {"id": "headline_metrics", "type": "metric-strip", "cardIds": ["card_ending_arr", "card_active_customers", "card_nrr"]},
            {
                "id": "growth_heading",
                "type": "markdown",
                "sourceId": "src_monthly",
                "body": "## Revenue growth was sustained across the full period\n\nEnding ARR increased throughout 36 observed months rather than depending on one endpoint jump. The December 2025 run-rate reached ₹150.9 crore. **So what:** the modeled business has both scale and momentum, but the source of that growth determines how durable it is.",
            },
            {"id": "growth_chart", "type": "chart", "chartId": "chart_monthly_arr"},
            {
                "id": "channel_heading",
                "type": "markdown",
                "sourceId": "src_channels",
                "body": "## Partner leads the run-rate; Outbound needs tighter quality controls\n\nPartner finished first at ₹39.5 crore of ending ARR. Outbound reached ₹39.1 crore, but its 14.1% observed logo churn was the highest of the five channels. **So what:** protect Partner capacity and investigate Outbound qualification, integration fit, and implementation readiness before adding more volume.",
            },
            {"id": "channel_chart", "type": "chart", "chartId": "chart_channels"},
            {"id": "channel_table", "type": "table", "tableId": "table_channels"},
            {
                "id": "retention_heading",
                "type": "markdown",
                "sourceId": "src_growth",
                "body": "## Post-sale growth keeps net retention above 100%\n\nNew business remained the largest 2025 ARR engine, while expansion, upgrades, and reactivation added another ₹12.0 crore. Combined with 94.4% GRR, this explains why NRR was only slightly above 100%. **So what:** manage NRR and GRR together so expansion does not hide avoidable churn.",
            },
            {"id": "growth_engine_chart", "type": "chart", "chartId": "chart_growth_engines"},
            {
                "id": "churn_heading",
                "type": "markdown",
                "sourceId": "src_churn",
                "body": "## Integration and adoption issues are the clearest retention themes\n\nMissing integrations and low adoption together represented 60.8% of modeled ARR lost to permanent churn. **So what:** instrument integration activation and onboarding milestones during the first six months, then target customer-success intervention before risk becomes permanent churn.",
            },
            {"id": "churn_chart", "type": "chart", "chartId": "chart_churn_reasons"},
            {
                "id": "recommendations",
                "type": "markdown",
                "body": "## Recommended next steps\n\n1. Prioritize Partner and Events for Enterprise acquisition while adding real pipeline and spend data before reallocating budget.\n2. Tighten Outbound qualification around integration requirements and implementation readiness.\n3. Instrument onboarding and integration activation in the first six months.\n4. Build a Professional-to-Enterprise upgrade signal using seat and integration growth.\n5. Review NRR beside GRR and permanent-churn reasons each month.",
            },
            {
                "id": "further_questions",
                "type": "markdown",
                "body": "## Further questions\n\n- Does channel quality remain after normalizing for customer tenure, industry, and initial contract size?\n- Which onboarding milestones best predict permanent churn versus temporary suspension?\n- How do CAC, payback, sales-cycle length, and win rate change the channel recommendation?",
            },
            {
                "id": "caveats",
                "type": "markdown",
                "body": "## Caveats and assumptions\n\nThis report uses deterministic synthetic data. ARR is a modeled MRR run-rate, not audited revenue. Channel comparisons are descriptive and have different exposure periods. Funnel, CAC, quota, and sales-cycle metrics are out of scope because the four-table model has no lead, opportunity, activity, marketing-spend, or quota facts.",
            },
        ],
    }
    artifact = {
        "surface": "report",
        "manifest": manifest,
        "snapshot": {
            "version": 1,
            "status": "ready",
            "generatedAt": GENERATED_AT,
            "datasets": {
                "kpis": kpis,
                "monthly_growth": monthly,
                "channel_performance": channels,
                "growth_events_2025": growth,
                "churn_reasons": churn,
            },
        },
        "sources": sources,
        "package_info": {
            "synthetic": True,
            "snapshot_label": "Deterministic portfolio snapshot through December 2025",
        },
    }
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / "artifact.json").write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"artifact": "report/artifact.json", "datasets": {key: len(value) for key, value in artifact["snapshot"]["datasets"].items()}}, indent=2))


if __name__ == "__main__":
    main()
