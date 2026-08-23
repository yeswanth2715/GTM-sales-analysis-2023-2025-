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


def build_dashboard(root: Path, metrics: dict, monthly: list[dict], channels: list[dict], churn: list[dict]) -> str:
    body: list[str] = []
    body.append(rect(0, 0, 1600, 116, INK, 0))
    body.append(text(56, 58, "B2B SaaS Revenue Growth & GTM Performance", 34, 700, WHITE))
    body.append(text(56, 89, "Synthetic CRM portfolio analysis · Jan 2023–Dec 2025 · INR", 16, 400, "#C9D2E3"))
    body.append(text(1544, 67, "Portfolio Project", 15, 600, "#C9D2E3", "end"))

    card(body, 56, 144, 340, 132, "Ending ARR", rupee_crore(metrics["ending_arr_inr"]), BLUE, "December 2025 run-rate")
    card(body, 416, 144, 340, 132, "Active customers", f'{metrics["ending_active_customers"]:,}', GOLD, "Professional + Enterprise")
    card(body, 776, 144, 340, 132, "2025 NRR", f'{metrics["nrr_2025_pct"]:.1f}%', OLIVE, f'GRR {metrics["grr_2025_pct"]:.1f}%')
    card(body, 1136, 144, 408, 132, "Two-year MRR growth", f'+{metrics["two_year_mrr_growth_pct"]:.1f}%', ORANGE, "Dec 2023 to Dec 2025")

    draw_line_chart(body, monthly, 56, 304, 936, 404)
    draw_channel_bars(body, channels, 1016, 304, 528, 404)
    draw_growth_bars(body, metrics, 56, 736, 744, 340)
    draw_churn_bars(body, churn, 824, 736, 720, 340)
    body.append(text(56, 1108, "Key read: Partner leads ending ARR; Outbound scales nearly as much but has the highest observed logo churn.", 17, 600, INK))
    body.append(text(56, 1137, "Source: deterministic synthetic data generated in-repo. NRR uses the prior December customer cohort; reactivations are excluded from permanent churn.", 14, 400, MUTED))
    return svg_document(1600, 1170, body)


def build_linkedin(root: Path, metrics: dict, monthly: list[dict], channels: list[dict]) -> str:
    body: list[str] = []
    body.append(rect(0, 0, 1200, 164, INK, 0))
    body.append(text(64, 64, "PORTFOLIO PROJECT", 18, 700, GOLD))
    body.append(text(64, 108, "B2B SaaS Revenue Growth", 36, 700, WHITE))
    body.append(text(64, 143, "& GTM Performance Analysis", 36, 700, WHITE))

    card(body, 64, 198, 500, 142, "Ending ARR", rupee_crore(metrics["ending_arr_inr"]), BLUE, "December 2025 run-rate")
    card(body, 588, 198, 548, 142, "2025 net revenue retention", f'{metrics["nrr_2025_pct"]:.1f}%', OLIVE, f'Gross retention: {metrics["grr_2025_pct"]:.1f}%')
    card(body, 64, 364, 500, 142, "Active customers", f'{metrics["ending_active_customers"]:,}', GOLD, "Professional + Enterprise")
    card(body, 588, 364, 548, 142, "Two-year MRR growth", f'+{metrics["two_year_mrr_growth_pct"]:.1f}%', ORANGE, "Dec 2023 to Dec 2025")

    body.append(rect(64, 542, 1072, 350, WHITE, 18, GRID))
    body.append(text(94, 586, "Monthly ending ARR", 22, 700))
    body.append(text(94, 614, "36 observed months · INR crore", 15, 400, MUTED))
    values = [float(row["ending_arr_inr"]) for row in monthly]
    plot_x, plot_y, plot_w, plot_h = 112, 650, 976, 176
    maximum = max(values) * 1.08
    for tick in range(4):
        yy = plot_y + plot_h - plot_h * tick / 3
        body.append(line(plot_x, yy, plot_x + plot_w, yy, GRID, 1))
    points = []
    for index, value in enumerate(values):
        px = plot_x + plot_w * index / (len(values) - 1)
        py = plot_y + plot_h - value / maximum * plot_h
        points.append((px, py))
    path = "M " + " ".join(f"{px:.1f} {py:.1f}" if i == 0 else f"L {px:.1f} {py:.1f}" for i, (px, py) in enumerate(points))
    body.append(f'<path d="{path}" fill="none" stroke="{BLUE}" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>')
    body.append(text(plot_x, 856, "Jan ’23", 14, 400, MUTED))
    body.append(text(plot_x + plot_w, 856, "Dec ’25", 14, 400, MUTED, "end"))
    body.append(text(points[-1][0], points[-1][1] - 16, rupee_crore(values[-1]), 16, 700, BLUE, "end"))

    body.append(text(64, 950, "What the analysis found", 28, 700, INK))
    findings = [
        f'Partner finished #1 with {rupee_crore(float(channels[0]["ending_arr_inr"]))} ending ARR.',
        f'Outbound reached similar scale, but observed logo churn was {float(next(r for r in channels if r["acquisition_channel"] == "Outbound")["observed_logo_churn_pct"]):.1f}%.',
        f'Expansion, upgrades and reactivation added {rupee_crore(metrics["expansion_arr_2025_inr"] + metrics["upgrade_arr_2025_inr"] + metrics["reactivated_arr_2025_inr"])} in 2025 ARR.',
        "Missing integrations were the largest permanent-churn reason by ARR lost.",
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

    dashboard = build_dashboard(root, metrics, monthly, channels, churn)
    linkedin = build_linkedin(root, metrics, monthly, channels)
    (assets_dir / "dashboard_preview.svg").write_text(dashboard, encoding="utf-8")
    (assets_dir / "linkedin_project_summary.svg").write_text(linkedin, encoding="utf-8")
    print(json.dumps({"dashboard": "assets/dashboard_preview.svg", "linkedin": "assets/linkedin_project_summary.svg"}, indent=2))


if __name__ == "__main__":
    main()
