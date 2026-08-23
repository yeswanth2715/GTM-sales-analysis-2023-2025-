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
    customer_flow_raw = csv_rows("10_monthly_customer_growth_churn.csv")
    segment_churn_raw = csv_rows("11_segment_churn_retention.csv")
    growth_quality_raw = csv_rows("12_growth_quality_diagnostic.csv")

    kpis = [{
        "ending_arr_crore": round(metrics["ending_arr_inr"] / 10_000_000, 1),
        "ending_active_customers": metrics["ending_active_customers"],
        "nrr_2025_rate": metrics["nrr_2025_pct"] / 100,
        "grr_2025_rate": metrics["grr_2025_pct"] / 100,
        "two_year_mrr_growth_rate": metrics["two_year_mrr_growth_pct"] / 100,
        "arr_growth_2025_rate": metrics["arr_growth_2025_pct"] / 100,
        "arr_growth_2024_rate": metrics["arr_growth_2024_pct"] / 100,
        "active_customer_growth_2025_rate": metrics["active_customer_growth_2025_pct"] / 100,
        "highest_segment_churn_rate": metrics["highest_segment_observed_logo_churn_pct"] / 100,
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
    monthly_logo_flow = []
    growth_rate_comparison = []
    for row in customer_flow_raw:
        for flow_type, field in [
            ("New customers", "new_customers"),
            ("Permanent churn", "permanently_churned_customers"),
        ]:
            monthly_logo_flow.append({
                "revenue_month": row["revenue_month"],
                "flow_type": flow_type,
                "customer_count": as_number(row[field]),
                "active_customers": as_number(row["active_customers"]),
                "net_active_customer_change": as_number(row["net_active_customer_change"]),
            })
        if row["yoy_arr_growth_pct"] != "":
            growth_rate_comparison.extend([
                {
                    "revenue_month": row["revenue_month"],
                    "growth_series": "ARR growth",
                    "yoy_growth_rate": as_number(row["yoy_arr_growth_pct"]) / 100,
                },
                {
                    "revenue_month": row["revenue_month"],
                    "growth_series": "Active-customer growth",
                    "yoy_growth_rate": as_number(row["yoy_active_customer_growth_pct"]) / 100,
                },
            ])
    segment_churn = []
    for row in segment_churn_raw:
        segment_churn.append({
            "company_segment": row["company_segment"],
            "starting_plan_tier": row["starting_plan_tier"],
            "acquired_customers": as_number(row["acquired_customers"]),
            "permanently_churned_customers": as_number(row["permanently_churned_customers"]),
            "observed_logo_churn_rate": as_number(row["observed_logo_churn_pct"]) / 100,
            "active_customers_dec_2025": as_number(row["active_customers_dec_2025"]),
            "ending_arr_crore": round(as_number(row["ending_arr_inr"]) / 10_000_000, 2),
            "permanent_churn_arr_lost_crore": round(as_number(row["permanent_churn_arr_lost_inr"]) / 10_000_000, 2),
            "avg_arr_per_active_customer_crore": round(as_number(row["avg_arr_per_active_customer_inr"]) / 10_000_000, 3),
        })
    growth_quality = []
    for row in growth_quality_raw:
        growth_quality.append({
            "year": as_number(row["year"]),
            "ending_arr_crore": round(as_number(row["ending_arr_inr"]) / 10_000_000, 2),
            "active_customers": as_number(row["active_customers"]),
            "avg_arr_per_active_customer_crore": round(as_number(row["avg_arr_per_active_customer_inr"]) / 10_000_000, 3),
            "new_customers": as_number(row["new_customers"]),
            "permanently_churned_customers": as_number(row["permanently_churned_customers"]),
            "net_new_minus_permanent_churn": as_number(row["net_new_minus_permanent_churn"]),
            "post_sale_added_arr_crore": round(as_number(row["post_sale_added_arr_inr"]) / 10_000_000, 2),
            "yoy_arr_growth_rate": None if row["yoy_arr_growth_pct"] == "" else as_number(row["yoy_arr_growth_pct"]) / 100,
            "yoy_active_customer_growth_rate": None if row["yoy_active_customer_growth_pct"] == "" else as_number(row["yoy_active_customer_growth_pct"]) / 100,
            "yoy_avg_arr_per_customer_growth_rate": None if row["yoy_avg_arr_per_customer_growth_pct"] == "" else as_number(row["yoy_avg_arr_per_customer_growth_pct"]) / 100,
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
        source(
            "src_customer_flow", "Monthly customer growth and churn query", "10_monthly_customer_growth_churn.sql",
            "Compares monthly customer acquisition, reactivation, permanent churn, active-customer movement, ARR, and average ARR per active customer.",
            ["revenue", "churn"],
            ["Revenue months from 2023-01-01 through 2025-12-01", "Permanent churn is grouped to calendar month"],
            {
                "Net active customer change": "Current month active customers minus prior month active customers.",
                "YoY ARR growth": "Ending ARR change versus the same month one year earlier.",
                "YoY active-customer growth": "Active-customer change versus the same month one year earlier.",
            },
        ),
        source(
            "src_segment_churn", "Segment churn and retention query", "11_segment_churn_retention.sql",
            "Compares permanent logo churn, ending ARR, and ARR lost across customer segments and starting plans.",
            ["customers", "products", "revenue", "churn"],
            ["Ending ARR is measured at 2025-12-01", "Plan tier is the customer's starting plan", "Permanent churn is observed over the full modeled history"],
            {"Observed segment logo churn": "Permanently churned customers divided by all acquired customers in the segment and starting-plan group; not annualized."},
        ),
        source(
            "src_growth_quality", "Annual growth quality diagnostic", "12_growth_quality_diagnostic.sql",
            "Separates annual ARR growth into active-customer growth and average ARR per active customer while retaining acquisition, churn, and post-sale growth context.",
            ["revenue", "churn"],
            ["Calendar years 2023 through 2025", "Year-end metrics use each December"],
            {
                "YoY ARR growth": "December ending ARR change versus the previous December.",
                "YoY active-customer growth": "December active-customer change versus the previous December.",
                "Average ARR per active customer": "December ending ARR divided by December active customers.",
            },
        ),
    ]

    title = "B2B SaaS Revenue Growth & GTM Performance"
    manifest = {
        "version": 1,
        "surface": "report",
        "title": title,
        "description": "A decision-ready analysis of recurring-revenue growth quality, customer additions and churn, segment retention, acquisition-channel quality, and post-sale expansion in a fictional B2B SaaS CRM.",
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
            {
                "id": "card_arr_growth",
                "description": "Year-over-year ending ARR growth slowed in 2025 while remaining positive.",
                "dataset": "kpis",
                "sourceId": "src_growth_quality",
                "metrics": [
                    {"label": "2025 ARR growth", "field": "arr_growth_2025_rate", "format": "percent", "signed": True},
                    {"label": "2024 ARR growth", "field": "arr_growth_2024_rate", "format": "percent", "signed": True},
                ],
            },
            {
                "id": "card_segment_churn",
                "description": "Mid-Market customers starting on Professional had the higher observed permanent logo churn.",
                "dataset": "kpis",
                "sourceId": "src_segment_churn",
                "metrics": [
                    {"label": "Highest segment churn", "field": "highest_segment_churn_rate", "format": "percent"},
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
            {
                "id": "chart_growth_rates",
                "title": "Year-over-year ARR and active-customer growth",
                "description": "Monthly year-over-year rates from January 2024 through December 2025.",
                "type": "line",
                "dataset": "growth_rate_comparison",
                "sourceId": "src_customer_flow",
                "encodings": {
                    "x": {"field": "revenue_month", "type": "temporal", "title": "Month"},
                    "y": {"field": "yoy_growth_rate", "type": "quantitative", "title": "Year-over-year growth"},
                    "color": {"field": "growth_series", "type": "nominal", "title": "Growth measure"},
                },
                "options": {"legend": {"show": True}, "palette": {"kind": "categorical", "colors": ["#2563EB", "#D9A441"]}},
            },
            {
                "id": "chart_logo_flow",
                "title": "Monthly new customers and permanent churn",
                "description": "Logo flows from January 2023 through December 2025; temporary suspensions are not permanent churn.",
                "type": "line",
                "dataset": "monthly_logo_flow",
                "sourceId": "src_customer_flow",
                "encodings": {
                    "x": {"field": "revenue_month", "type": "temporal", "title": "Month"},
                    "y": {"field": "customer_count", "type": "quantitative", "title": "Customers"},
                    "color": {"field": "flow_type", "type": "nominal", "title": "Customer flow"},
                },
                "options": {"legend": {"show": True}, "palette": {"kind": "categorical", "colors": ["#2563EB", "#C45C88"]}},
            },
            {
                "id": "chart_segment_churn",
                "title": "Observed permanent logo churn by customer segment",
                "description": "Full modeled history; denominator is all acquired customers in each segment and starting-plan group.",
                "type": "bar",
                "dataset": "segment_churn",
                "sourceId": "src_segment_churn",
                "encodings": {
                    "x": {"field": "company_segment", "type": "nominal", "title": "Customer segment"},
                    "y": {"field": "observed_logo_churn_rate", "type": "quantitative", "title": "Observed logo churn"},
                },
                "options": {"orientation": "vertical", "grouping": "grouped", "legend": {"show": False}, "palette": {"kind": "single", "colors": ["#C45C88"]}},
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
            },
            {
                "id": "table_segment_churn",
                "title": "Customer segment churn detail",
                "description": "Permanent churn and December 2025 portfolio scale by segment and starting plan.",
                "dataset": "segment_churn",
                "sourceId": "src_segment_churn",
                "columns": [
                    {"field": "company_segment", "label": "Segment"},
                    {"field": "starting_plan_tier", "label": "Starting plan"},
                    {"field": "acquired_customers", "label": "Acquired customers", "format": "number"},
                    {"field": "permanently_churned_customers", "label": "Permanent churn", "format": "number"},
                    {"field": "observed_logo_churn_rate", "label": "Observed logo churn", "format": "percent"},
                    {"field": "ending_arr_crore", "label": "Ending ARR", "format": "number", "unit": "₹ crore"},
                    {"field": "permanent_churn_arr_lost_crore", "label": "ARR lost", "format": "number", "unit": "₹ crore"},
                ],
                "defaultSort": {"field": "observed_logo_churn_rate", "direction": "desc"},
            },
            {
                "id": "table_growth_quality",
                "title": "Annual growth quality detail",
                "description": "Year-end scale, customer growth, churn, and post-sale contribution from 2023 through 2025.",
                "dataset": "growth_quality",
                "sourceId": "src_growth_quality",
                "columns": [
                    {"field": "year", "label": "Year", "format": "number"},
                    {"field": "ending_arr_crore", "label": "Ending ARR", "format": "number", "unit": "₹ crore"},
                    {"field": "active_customers", "label": "Active customers", "format": "number"},
                    {"field": "new_customers", "label": "New customers", "format": "number"},
                    {"field": "permanently_churned_customers", "label": "Permanent churn", "format": "number"},
                    {"field": "yoy_arr_growth_rate", "label": "YoY ARR growth", "format": "percent", "movement": True},
                    {"field": "yoy_active_customer_growth_rate", "label": "YoY customer growth", "format": "percent", "movement": True},
                    {"field": "yoy_avg_arr_per_customer_growth_rate", "label": "YoY avg ARR/customer growth", "format": "percent", "movement": True},
                ],
                "defaultSort": {"field": "year", "direction": "asc"},
            }
        ],
        "blocks": [
            {"id": "title", "type": "markdown", "body": f"# {title}"},
            {
                "id": "executive_summary",
                "type": "markdown",
                "body": "## Executive Summary\n\n- **The business is still growing, but momentum is slowing.** Year-over-year ARR growth fell from 71.0% in 2024 to 47.7% in 2025; active-customer growth also slowed to 41.3%.\n- **Customer count did not decline.** Active customers rose every observed month and finished at 489, while 2025 added 163 new customers and recorded 27 permanent churns.\n- **Growth is not only a logo-volume story.** Average ARR per active customer increased 4.5% in 2025, and expansion, upgrades, and reactivation added ₹12.0 crore.\n- **Churn risk differs by segment and channel.** Mid-Market customers starting on Professional had 8.3% observed permanent logo churn versus 6.6% for Large Enterprise; Outbound remained the highest-churn channel.",
            },
            {"id": "headline_metrics", "type": "metric-strip", "cardIds": ["card_ending_arr", "card_active_customers", "card_nrr", "card_arr_growth", "card_segment_churn"]},
            {
                "id": "growth_heading",
                "type": "markdown",
                "sourceId": "src_monthly",
                "body": "## Revenue growth was sustained across the full period\n\nEnding ARR increased throughout 36 observed months rather than depending on one endpoint jump. The December 2025 run-rate reached ₹150.9 crore. **So what:** the modeled business has both scale and momentum, but the source of that growth determines how durable it is.",
            },
            {"id": "growth_chart", "type": "chart", "chartId": "chart_monthly_arr"},
            {
                "id": "growth_quality_heading",
                "type": "markdown",
                "sourceId": "src_customer_flow",
                "body": "## Growth remains positive, but both revenue and customer momentum are decelerating\n\nARR grew faster than the active-customer base throughout the comparable period, showing that customer mix, expansion, upgrades, and reactivation supported growth beyond logo acquisition. However, year-over-year ARR growth declined from 71.0% at December 2024 to 47.7% at December 2025, while active-customer growth declined from 60.2% to 41.3%. **So what:** leaders should not confuse a rising ARR line with accelerating growth; the correct operating question is whether acquisition and post-sale expansion can sustain momentum as the base becomes larger.",
            },
            {"id": "growth_rate_chart", "type": "chart", "chartId": "chart_growth_rates"},
            {"id": "growth_quality_table", "type": "table", "tableId": "table_growth_quality"},
            {
                "id": "customer_flow_heading",
                "type": "markdown",
                "sourceId": "src_customer_flow",
                "body": "## New customer additions remained above permanent churn every month\n\nThe active-customer base increased in every observed month. In 2025, 163 new customers entered the portfolio and 27 customers permanently churned; monthly permanent churn peaked at four customers while new additions ranged from 11 to 16. **So what:** there is no current logo-contraction signal in this synthetic scenario, but the higher 2025 churn volume should be monitored because absolute churn naturally becomes more material as the installed base grows.",
            },
            {"id": "logo_flow_chart", "type": "chart", "chartId": "chart_logo_flow"},
            {
                "id": "segment_churn_heading",
                "type": "markdown",
                "sourceId": "src_segment_churn",
                "body": "## Mid-Market customers show the higher permanent logo-churn rate\n\nMid-Market customers starting on Professional recorded 25 permanent churns from 301 acquired customers, an observed rate of 8.3%. Large Enterprise customers starting on Enterprise recorded 15 churns from 228 customers, or 6.6%. Large Enterprise still lost more ARR—₹6.7 crore versus ₹4.7 crore—because each account carried more value. **So what:** Mid-Market needs broader logo-retention controls, while Enterprise needs high-touch prevention for fewer but more financially material losses.",
            },
            {"id": "segment_churn_chart", "type": "chart", "chartId": "chart_segment_churn"},
            {"id": "segment_churn_table", "type": "table", "tableId": "table_segment_churn"},
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
                "body": "## Recommended next steps\n\n1. Add a monthly growth-quality review that tracks ARR growth, active-customer growth, average ARR per customer, new logos, permanent churn, NRR, and GRR together.\n2. Build a Mid-Market retention playbook focused on early adoption and integration activation, while using high-touch intervention for high-value Enterprise risks.\n3. Tighten Outbound qualification around integration requirements and implementation readiness.\n4. Preserve Partner and Events as priority Enterprise acquisition channels while adding real pipeline and spend data before reallocating budget.\n5. Build a Professional-to-Enterprise upgrade signal using seat and integration growth.",
            },
            {
                "id": "further_questions",
                "type": "markdown",
                "body": "## Further questions\n\n- Does segment churn remain different after normalizing for tenure, industry, contract size, and acquisition channel?\n- Which onboarding milestones best predict permanent churn versus temporary suspension?\n- How much of average ARR-per-customer growth comes from expansion versus plan upgrades?\n- How do lead volume, win rate, CAC, payback, and sales-cycle length change the channel recommendation?",
            },
            {
                "id": "caveats",
                "type": "markdown",
                "body": "## Caveats and assumptions\n\nThis report uses deterministic synthetic data. ARR is a modeled MRR run-rate, not audited revenue. Segment and channel churn rates are descriptive full-history portfolio ratios with unequal exposure time, not annualized churn rates. Starting plan is used for the segment denominator so upgrades do not redefine the original cohort. Funnel, CAC, quota, and sales-cycle metrics remain out of scope because the four-table model has no lead, opportunity, activity, marketing-spend, or quota facts.",
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
                "monthly_logo_flow": monthly_logo_flow,
                "growth_rate_comparison": growth_rate_comparison,
                "segment_churn": segment_churn,
                "growth_quality": growth_quality,
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
