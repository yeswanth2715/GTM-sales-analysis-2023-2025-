#!/usr/bin/env python3
"""Build dependency-free SVG portfolio visuals from reviewed query outputs."""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path


INK = "#172033"
MUTED = "#667085"
GRID = "#E7EAF0"
BLUE = "#2563EB"
GOLD = "#D9A441"
ORANGE = "#E27D3F"
OLIVE = "#6B7D3A"
PINK = "#C45C88"
PALE_BLUE = "#EAF1FF"
BG = "#F6F8FC"
WHITE = "#FFFFFF"


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def crore(value: float) -> float:
    return value / 10_000_000


def rupee_crore(value: float, decimals: int = 1) -> str:
    return f"₹{crore(value):.{decimals}f}cr"


def text(x: float, y: float, value: str, size: int = 24, weight: int = 400, fill: str = INK, anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="DejaVu Sans, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'
        f'{html.escape(str(value))}</text>'
    )


def rect(x: float, y: float, width: float, height: float, fill: str, radius: float = 18, stroke: str = "none") -> str:
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{dash_attr}/>'


def svg_document(width: int, height: int, body: list[str]) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" fill="{BG}"/>'
        + "".join(body)
        + "</svg>\n"
    )


def card(body: list[str], x: int, y: int, width: int, height: int, title: str, value: str, accent: str, note: str) -> None:
    body.append(rect(x, y, width, height, WHITE, 18, GRID))
    body.append(rect(x, y, 8, height, accent, 4))
    body.append(text(x + 28, y + 40, title, 18, 600, MUTED))
    body.append(text(x + 28, y + 86, value, 34, 700, INK))
    body.append(text(x + 28, y + 116, note, 15, 400, MUTED))


def draw_line_chart(body: list[str], rows: list[dict], x: int, y: int, width: int, height: int) -> None:
    body.append(rect(x, y, width, height, WHITE, 18, GRID))
    body.append(text(x + 28, y + 40, "Monthly ending ARR", 22, 700))
    body.append(text(x + 28, y + 67, "Jan 2023–Dec 2025 · INR crore", 15, 400, MUTED))
    values = [float(row["ending_arr_inr"]) for row in rows]
    plot_x, plot_y = x + 74, y + 95
    plot_w, plot_h = width - 108, height - 145
    minimum = 0
    maximum = max(values) * 1.08
    for tick in range(5):
        value = maximum * tick / 4
        yy = plot_y + plot_h - plot_h * tick / 4
        body.append(line(plot_x, yy, plot_x + plot_w, yy, GRID, 1))
        body.append(text(plot_x - 12, yy + 5, f"{crore(value):.0f}", 13, 400, MUTED, "end"))
    points = []
    for index, value in enumerate(values):
        px = plot_x + plot_w * index / (len(values) - 1)
        py = plot_y + plot_h - (value - minimum) / (maximum - minimum) * plot_h
        points.append((px, py))
    area_path = f"M {points[0][0]:.1f} {plot_y + plot_h:.1f} " + " ".join(
        f"L {px:.1f} {py:.1f}" for px, py in points
    ) + f" L {points[-1][0]:.1f} {plot_y + plot_h:.1f} Z"
    body.append(f'<path d="{area_path}" fill="{PALE_BLUE}" opacity="0.9"/>')
    path = "M " + " ".join(f"{px:.1f} {py:.1f}" if i == 0 else f"L {px:.1f} {py:.1f}" for i, (px, py) in enumerate(points))
    body.append(f'<path d="{path}" fill="none" stroke="{BLUE}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>')
    for index in [0, 11, 23, 35]:
        px, py = points[index]
        body.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="{WHITE}" stroke="{BLUE}" stroke-width="3"/>')
    for index, label in [(0, "Jan ’23"), (11, "Dec ’23"), (23, "Dec ’24"), (35, "Dec ’25")]:
        px, _ = points[index]
        body.append(text(px, plot_y + plot_h + 28, label, 13, 400, MUTED, "middle"))
    body.append(text(points[-1][0] - 4, points[-1][1] - 14, rupee_crore(values[-1]), 15, 700, BLUE, "end"))


def draw_channel_bars(body: list[str], rows: list[dict], x: int, y: int, width: int, height: int) -> None:
    body.append(rect(x, y, width, height, WHITE, 18, GRID))
    body.append(text(x + 28, y + 40, "Ending ARR by acquisition channel", 22, 700))
    body.append(text(x + 28, y + 67, "December 2025 · INR crore", 15, 400, MUTED))
    max_value = max(float(row["ending_arr_inr"]) for row in rows)
    colors = [BLUE, GOLD, ORANGE, OLIVE, PINK]
    start_y = y + 105
    label_w = 95
    bar_w = width - 210
    for index, row in enumerate(rows):
        yy = start_y + index * 54
        value = float(row["ending_arr_inr"])
        body.append(text(x + 28, yy + 19, row["acquisition_channel"], 15, 600, INK))
        body.append(rect(x + 28 + label_w, yy, bar_w, 24, "#EEF1F5", 8))
        body.append(rect(x + 28 + label_w, yy, bar_w * value / max_value, 24, colors[index], 8))
        body.append(text(x + width - 30, yy + 19, rupee_crore(value), 14, 700, INK, "end"))


def draw_growth_bars(body: list[str], metrics: dict, x: int, y: int, width: int, height: int) -> None:
    body.append(rect(x, y, width, height, WHITE, 18, GRID))
    body.append(text(x + 28, y + 40, "2025 ARR growth engines", 22, 700))
    body.append(text(x + 28, y + 67, "Added ARR by movement type · INR crore", 15, 400, MUTED))
    values = [
        ("New business", metrics["new_arr_2025_inr"], BLUE),
        ("Expansion", metrics["expansion_arr_2025_inr"], GOLD),
        ("Upgrades", metrics["upgrade_arr_2025_inr"], ORANGE),
        ("Reactivation", metrics["reactivated_arr_2025_inr"], OLIVE),
    ]
    max_value = max(value for _, value, _ in values)
    plot_y = y + 108
    baseline = y + height - 46
    slot = (width - 76) / len(values)
    for index, (label, value, color) in enumerate(values):
        bar_height = (baseline - plot_y) * value / max_value
        xx = x + 40 + index * slot
        body.append(rect(xx, baseline - bar_height, slot - 28, bar_height, color, 8))
        body.append(text(xx + (slot - 28) / 2, baseline - bar_height - 12, rupee_crore(value), 14, 700, INK, "middle"))
        body.append(text(xx + (slot - 28) / 2, baseline + 25, label, 13, 600, MUTED, "middle"))


def draw_churn_bars(body: list[str], rows: list[dict], x: int, y: int, width: int, height: int) -> None:
    body.append(rect(x, y, width, height, WHITE, 18, GRID))
    body.append(text(x + 28, y + 40, "Permanent churn by reason", 22, 700))
    body.append(text(x + 28, y + 67, "ARR lost over 2023–2025 · INR crore", 15, 400, MUTED))
    max_value = max(float(row["arr_lost_inr"]) for row in rows)
    start_y = y + 100
    label_w = 174
    bar_w = width - 285
    for index, row in enumerate(rows):
        yy = start_y + index * 47
        value = float(row["arr_lost_inr"])
        label = {
            "Implementation Complexity": "Implementation",
            "Vendor Consolidation": "Vendor consolidation",
        }.get(row["churn_reason"], row["churn_reason"])
        body.append(text(x + 28, yy + 17, label, 13, 600, INK))
        body.append(rect(x + 28 + label_w, yy, bar_w, 21, "#F1F2F5", 7))
        body.append(rect(x + 28 + label_w, yy, bar_w * value / max_value, 21, PINK, 7))
        body.append(text(x + width - 28, yy + 17, rupee_crore(value), 13, 700, INK, "end"))


def draw_growth_quality_lines(body: list[str], rows: list[dict], x: int, y: int, width: int, height: int) -> None:
    comparable = [row for row in rows if row["yoy_arr_growth_pct"]]
    body.append(rect(x, y, width, height, WHITE, 18, GRID))
    body.append(text(x + 28, y + 40, "Year-over-year growth quality", 22, 700))
    body.append(text(x + 28, y + 67, "ARR growth vs active-customer growth · Jan 2024–Dec 2025", 15, 400, MUTED))
    plot_x, plot_y = x + 72, y + 104
    plot_w, plot_h = width - 112, height - 160
    maximum = max(max(float(row["yoy_arr_growth_pct"]), float(row["yoy_active_customer_growth_pct"])) for row in comparable) * 1.08
    for tick in range(5):
        value = maximum * tick / 4
        yy = plot_y + plot_h - plot_h * tick / 4
        body.append(line(plot_x, yy, plot_x + plot_w, yy, GRID, 1))
        body.append(text(plot_x - 12, yy + 5, f"{value:.0f}%", 13, 400, MUTED, "end"))
    series = [
        ("yoy_arr_growth_pct", "ARR growth", BLUE),
        ("yoy_active_customer_growth_pct", "Customer growth", GOLD),
    ]
    for field, _, color in series:
        points = []
        for index, row in enumerate(comparable):
            value = float(row[field])
            px = plot_x + plot_w * index / (len(comparable) - 1)
            py = plot_y + plot_h - value / maximum * plot_h
            points.append((px, py))
        path = "M " + " ".join(f"{px:.1f} {py:.1f}" if i == 0 else f"L {px:.1f} {py:.1f}" for i, (px, py) in enumerate(points))
        body.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>')
        body.append(f'<circle cx="{points[-1][0]:.1f}" cy="{points[-1][1]:.1f}" r="5" fill="{WHITE}" stroke="{color}" stroke-width="3"/>')
        body.append(text(points[-1][0] - 3, points[-1][1] - 12, f'{float(comparable[-1][field]):.1f}%', 13, 700, color, "end"))
    body.append(line(x + 30, y + height - 28, x + 54, y + height - 28, BLUE, 4))
    body.append(text(x + 62, y + height - 23, "ARR growth", 13, 600, MUTED))
    body.append(line(x + 160, y + height - 28, x + 184, y + height - 28, GOLD, 4))
    body.append(text(x + 192, y + height - 23, "Active-customer growth", 13, 600, MUTED))


def draw_customer_flow_lines(body: list[str], rows: list[dict], x: int, y: int, width: int, height: int) -> None:
    body.append(rect(x, y, width, height, WHITE, 18, GRID))
    body.append(text(x + 28, y + 40, "Monthly customer additions and churn", 22, 700))
    body.append(text(x + 28, y + 67, "New customers vs permanent churn · Jan 2023–Dec 2025", 15, 400, MUTED))
    plot_x, plot_y = x + 66, y + 98
    plot_w, plot_h = width - 100, height - 150
    maximum = max(float(row["new_customers"]) for row in rows) * 1.12
    for tick in range(4):
        value = maximum * tick / 3
        yy = plot_y + plot_h - plot_h * tick / 3
        body.append(line(plot_x, yy, plot_x + plot_w, yy, GRID, 1))
        body.append(text(plot_x - 10, yy + 5, f"{value:.0f}", 12, 400, MUTED, "end"))
    for field, color in [("new_customers", BLUE), ("permanently_churned_customers", PINK)]:
        points = []
        for index, row in enumerate(rows):
            value = float(row[field])
            px = plot_x + plot_w * index / (len(rows) - 1)
            py = plot_y + plot_h - value / maximum * plot_h
            points.append((px, py))
        path = "M " + " ".join(f"{px:.1f} {py:.1f}" if i == 0 else f"L {px:.1f} {py:.1f}" for i, (px, py) in enumerate(points))
        body.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>')
    body.append(line(x + 30, y + height - 26, x + 54, y + height - 26, BLUE, 4))
    body.append(text(x + 62, y + height - 21, "New customers", 13, 600, MUTED))
    body.append(line(x + 180, y + height - 26, x + 204, y + height - 26, PINK, 4))
    body.append(text(x + 212, y + height - 21, "Permanent churn", 13, 600, MUTED))


def draw_segment_churn(body: list[str], rows: list[dict], x: int, y: int, width: int, height: int) -> None:
    body.append(rect(x, y, width, height, WHITE, 18, GRID))
    body.append(text(x + 28, y + 40, "Observed permanent churn by segment", 22, 700))
    body.append(text(x + 28, y + 67, "Full-history logo churn; starting plan fixes the cohort", 15, 400, MUTED))
    maximum = max(float(row["observed_logo_churn_pct"]) for row in rows) * 1.25
    start_y = y + 112
    label_w = 164
    bar_w = width - 288
    for index, row in enumerate(rows):
        yy = start_y + index * 82
        value = float(row["observed_logo_churn_pct"])
        body.append(text(x + 28, yy + 18, row["company_segment"], 15, 600, INK))
        body.append(text(x + 28, yy + 40, f'Started on {row["starting_plan_tier"]}', 12, 400, MUTED))
        body.append(rect(x + 28 + label_w, yy, bar_w, 25, "#F1F2F5", 8))
        body.append(rect(x + 28 + label_w, yy, bar_w * value / maximum, 25, PINK, 8))
        body.append(text(x + width - 28, yy + 19, f"{value:.1f}%", 14, 700, INK, "end"))
        body.append(text(x + 28 + label_w, yy + 52, f'ARR lost {rupee_crore(float(row["permanent_churn_arr_lost_inr"]))}', 12, 500, MUTED))


def build_dashboard(root: Path, metrics: dict, monthly: list[dict], channels: list[dict], churn: list[dict], customer_flow: list[dict], segment_churn: list[dict]) -> str:
    body: list[str] = []
    body.append(rect(0, 0, 1600, 116, INK, 0))
    body.append(text(56, 58, "B2B SaaS Revenue Growth & GTM Performance", 34, 700, WHITE))
    body.append(text(56, 89, "Synthetic CRM portfolio analysis · Jan 2023–Dec 2025 · INR", 16, 400, "#C9D2E3"))
    body.append(text(1544, 67, "Portfolio Project", 15, 600, "#C9D2E3", "end"))

    card(body, 56, 144, 340, 132, "Ending ARR", rupee_crore(metrics["ending_arr_inr"]), BLUE, "December 2025 run-rate")
    card(body, 416, 144, 340, 132, "Active customers", f'{metrics["ending_active_customers"]:,}', GOLD, "Professional + Enterprise")
    card(body, 776, 144, 340, 132, "2025 ARR growth", f'+{metrics["arr_growth_2025_pct"]:.1f}%', OLIVE, f'2024: +{metrics["arr_growth_2024_pct"]:.1f}%')
    card(body, 1136, 144, 408, 132, "Highest segment churn", f'{metrics["highest_segment_observed_logo_churn_pct"]:.1f}%', ORANGE, "Mid-Market · started Professional")

    draw_line_chart(body, monthly, 56, 304, 744, 404)
    draw_growth_quality_lines(body, customer_flow, 824, 304, 720, 404)
    draw_customer_flow_lines(body, customer_flow, 56, 736, 744, 340)
    draw_segment_churn(body, segment_churn, 824, 736, 720, 340)
    body.append(text(56, 1108, "Key read: ARR and customer counts still rise, but both growth rates are slowing; new additions remain above permanent churn.", 17, 600, INK))
    body.append(text(56, 1137, "Source: deterministic synthetic data generated in-repo. Segment churn is a descriptive full-history ratio, not an annualized rate.", 14, 400, MUTED))
    return svg_document(1600, 1170, body)


def build_linkedin(root: Path, metrics: dict, monthly: list[dict], customer_flow: list[dict]) -> str:
    body: list[str] = []
    body.append(rect(0, 0, 1200, 164, INK, 0))
    body.append(text(64, 64, "PORTFOLIO PROJECT", 18, 700, GOLD))
    body.append(text(64, 108, "B2B SaaS Revenue Growth", 36, 700, WHITE))
    body.append(text(64, 143, "& GTM Performance Analysis", 36, 700, WHITE))

    card(body, 64, 198, 500, 142, "Ending ARR", rupee_crore(metrics["ending_arr_inr"]), BLUE, "December 2025 run-rate")
    card(body, 588, 198, 548, 142, "2025 ARR growth", f'+{metrics["arr_growth_2025_pct"]:.1f}%', OLIVE, f'2024: +{metrics["arr_growth_2024_pct"]:.1f}%')
    card(body, 64, 364, 500, 142, "Active customers", f'{metrics["ending_active_customers"]:,}', GOLD, "Professional + Enterprise")
    card(body, 588, 364, 548, 142, "Highest segment churn", f'{metrics["highest_segment_observed_logo_churn_pct"]:.1f}%', ORANGE, "Mid-Market · started Professional")

    body.append(rect(64, 542, 1072, 350, WHITE, 18, GRID))
    body.append(text(94, 586, "Growth quality: ARR versus active customers", 22, 700))
    body.append(text(94, 614, "Year-over-year growth · Jan 2024–Dec 2025", 15, 400, MUTED))
    rows = [row for row in customer_flow if row["yoy_arr_growth_pct"]]
    arr_values = [float(row["yoy_arr_growth_pct"]) for row in rows]
    customer_values = [float(row["yoy_active_customer_growth_pct"]) for row in rows]
    plot_x, plot_y, plot_w, plot_h = 112, 650, 976, 176
    maximum = max(arr_values + customer_values) * 1.08
    for tick in range(4):
        yy = plot_y + plot_h - plot_h * tick / 3
        body.append(line(plot_x, yy, plot_x + plot_w, yy, GRID, 1))
    for values, color in [(arr_values, BLUE), (customer_values, ORANGE)]:
        points = []
        for index, value in enumerate(values):
            px = plot_x + plot_w * index / (len(values) - 1)
            py = plot_y + plot_h - value / maximum * plot_h
            points.append((px, py))
        path = "M " + " ".join(f"{px:.1f} {py:.1f}" if i == 0 else f"L {px:.1f} {py:.1f}" for i, (px, py) in enumerate(points))
        body.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>')
    body.append(f'<circle cx="790" cy="604" r="6" fill="{BLUE}"/>')
    body.append(text(804, 610, "ARR growth", 13, 600, INK))
    body.append(f'<circle cx="922" cy="604" r="6" fill="{ORANGE}"/>')
    body.append(text(936, 610, "Customer growth", 13, 600, INK))
    body.append(text(plot_x, 856, "Jan ’24", 14, 400, MUTED))
    body.append(text(plot_x + plot_w, 856, "Dec ’25", 14, 400, MUTED, "end"))
    body.append(text(plot_x + plot_w, plot_y + plot_h - arr_values[-1] / maximum * plot_h - 14, f'{arr_values[-1]:.1f}%', 15, 700, BLUE, "end"))

    body.append(text(64, 950, "What the analysis found", 28, 700, INK))
    findings = [
        f'ARR growth slowed from {metrics["arr_growth_2024_pct"]:.1f}% in 2024 to {metrics["arr_growth_2025_pct"]:.1f}% in 2025.',
        "Active customers increased every month; the portfolio did not contract.",
        f'2025 added 163 customers and permanently churned {metrics["permanently_churned_customers_2025"]}.',
        "Mid-Market churned more logos; Enterprise churn carried more ARR per account.",
    ]
    for index, finding in enumerate(findings):
        yy = 1002 + index * 55
        body.append(f'<circle cx="78" cy="{yy - 7}" r="7" fill="{[BLUE, ORANGE, OLIVE, PINK][index]}"/>')
        body.append(text(102, yy, finding, 18, 500, INK))

    body.append(rect(64, 1234, 1072, 88, PALE_BLUE, 16))
    body.append(text(92, 1271, "Built with", 15, 700, BLUE))
    body.append(text(92, 1300, "SQL · SQLite · Python · Data modeling · KPI design · GTM analysis", 19, 600, INK))
    body.append(text(64, 1378, "Deterministic synthetic data · 4 related tables · 36 months · INR", 15, 400, MUTED))
    return svg_document(1200, 1420, body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    output_dir = root / "analysis" / "outputs"
    assets_dir = root / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    metrics = json.loads((output_dir / "headline_metrics.json").read_text(encoding="utf-8"))
    monthly = load_csv(output_dir / "03_monthly_revenue_growth.csv")
    channels = load_csv(output_dir / "04_gtm_channel_performance.csv")
    churn = load_csv(output_dir / "08_churn_reasons.csv")
    customer_flow = load_csv(output_dir / "10_monthly_customer_growth_churn.csv")
    segment_churn = load_csv(output_dir / "11_segment_churn_retention.csv")

    dashboard = build_dashboard(root, metrics, monthly, channels, churn, customer_flow, segment_churn)
    linkedin = build_linkedin(root, metrics, monthly, customer_flow)
    (assets_dir / "dashboard_preview.svg").write_text(dashboard, encoding="utf-8")
    (assets_dir / "linkedin_project_summary.svg").write_text(linkedin, encoding="utf-8")
    print(json.dumps({"dashboard": "assets/dashboard_preview.svg", "linkedin": "assets/linkedin_project_summary.svg"}, indent=2))


if __name__ == "__main__":
    main()
