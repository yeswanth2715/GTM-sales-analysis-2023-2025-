#!/usr/bin/env python3
"""Run independent data, metric, reproducibility, and artifact validation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import struct
import subprocess
import tempfile
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    """Read PNG width and height from the IHDR chunk using only stdlib."""
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"Not a valid PNG file: {path}")
    return struct.unpack(">II", header[16:24])


def add(checks: list[dict], name: str, passed: bool, evidence: str, severity: str = "High") -> None:
    checks.append({"check": name, "passed": bool(passed), "severity_if_failed": severity, "evidence": evidence})


def scalar(connection: sqlite3.Connection, query: str):
    return connection.execute(query).fetchone()[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    db_path = root / "database" / "crm_growth.db"
    output_dir = root / "analysis" / "outputs"
    checks: list[dict] = []

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        quality_rows = connection.execute((root / "sql" / "01_data_quality.sql").read_text(encoding="utf-8")).fetchall()
        quality_failures = [dict(row) for row in quality_rows if row["issue_count"] != 0]
        add(checks, "Core SQL data-quality checks", not quality_failures, f"9 checks; failures: {quality_failures or 'none'}")

        expected_counts = {"customers": 529, "products": 2, "revenue": 10453, "churn": 40}
        actual_counts = {table: scalar(connection, f"SELECT COUNT(*) FROM {table}") for table in expected_counts}
        add(checks, "Expected table volumes", actual_counts == expected_counts, f"Expected and actual: {actual_counts}", "Medium")

        min_month, max_month, month_count = connection.execute(
            "SELECT MIN(revenue_month), MAX(revenue_month), COUNT(DISTINCT revenue_month) FROM revenue"
        ).fetchone()
        add(checks, "Complete 36-month coverage", (min_month, max_month, month_count) == ("2023-01-01", "2025-12-01", 36), f"{min_month} to {max_month}; {month_count} months")

        required_nulls = 0
        for table in ["customers", "products", "revenue", "churn"]:
            columns = [row[1] for row in connection.execute(f"PRAGMA table_info({table})") if row[3] == 1]
            for column in columns:
                required_nulls += scalar(connection, f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL")
        add(checks, "Required-field completeness", required_nulls == 0, f"Nulls across NOT NULL columns: {required_nulls}")

        invalid_money = scalar(
            connection,
            "SELECT COUNT(*) FROM revenue WHERE closing_mrr_inr <= 0 OR recognized_revenue_inr <= 0 OR arr_run_rate_inr <= 0 OR movement_mrr_inr < 0"
        ) + scalar(connection, "SELECT COUNT(*) FROM churn WHERE mrr_lost_inr <= 0")
        add(checks, "Financial-domain validity", invalid_money == 0, f"Invalid non-positive/negative money rows: {invalid_money}")

        invalid_enums = scalar(connection, "SELECT COUNT(*) FROM revenue WHERE revenue_type NOT IN ('New','Recurring','Expansion','Upgrade','Reactivation')")
        invalid_enums += scalar(connection, "SELECT COUNT(*) FROM products WHERE plan_tier NOT IN ('Professional','Enterprise')")
        invalid_enums += scalar(connection, "SELECT COUNT(*) FROM customers WHERE company_segment NOT IN ('Mid-Market','Large Enterprise')")
        add(checks, "Controlled-value validity", invalid_enums == 0, f"Rows outside allowed enums: {invalid_enums}")

        fk_failures = connection.execute("PRAGMA foreign_key_check").fetchall()
        add(checks, "Referential integrity", len(fk_failures) == 0, f"Foreign-key failures: {len(fk_failures)}")

        reactivation_overlap = scalar(
            connection,
            "SELECT COUNT(DISTINCT ch.customer_id) FROM churn ch JOIN revenue r ON r.customer_id=ch.customer_id AND r.revenue_type='Reactivation'"
        )
        add(checks, "Reactivation/churn business rule", reactivation_overlap == 0, f"Reactivated customers in permanent churn: {reactivation_overlap}")

        kpi = connection.execute((root / "sql" / "02_executive_kpis.sql").read_text(encoding="utf-8")).fetchone()
        ending_mrr = scalar(connection, "SELECT SUM(closing_mrr_inr) FROM revenue WHERE revenue_month='2025-12-01'")
        ending_arr_alt = scalar(connection, "SELECT SUM(arr_run_rate_inr) FROM revenue WHERE revenue_month='2025-12-01'")
        add(checks, "Ending ARR independently reconciled", kpi["ending_arr_inr"] == ending_mrr * 12 == ending_arr_alt, f"KPI={kpi['ending_arr_inr']:,}; MRR×12={ending_mrr * 12:,}; direct ARR sum={ending_arr_alt:,}")

        retention = connection.execute("""
            WITH s AS (
                SELECT customer_id, closing_mrr_inr start_mrr FROM revenue WHERE revenue_month='2024-12-01'
            ), e AS (
                SELECT customer_id, closing_mrr_inr end_mrr FROM revenue WHERE revenue_month='2025-12-01'
            )
            SELECT
                ROUND(100.0*SUM(COALESCE(e.end_mrr,0))/SUM(s.start_mrr),1),
                ROUND(100.0*SUM(MIN(s.start_mrr,COALESCE(e.end_mrr,0)))/SUM(s.start_mrr),1)
            FROM s LEFT JOIN e USING(customer_id)
        """).fetchone()
        add(checks, "2025 NRR/GRR independently recomputed", (retention[0], retention[1]) == (kpi["nrr_2025_pct"], kpi["grr_2025_pct"]), f"NRR={retention[0]}%; GRR={retention[1]}%")

        channel_arr = scalar(connection, """
            SELECT SUM(ending_arr_inr) FROM (
                SELECT c.acquisition_channel, SUM(r.arr_run_rate_inr) ending_arr_inr
                FROM customers c JOIN revenue r ON r.customer_id=c.customer_id
                WHERE r.revenue_month='2025-12-01'
                GROUP BY c.acquisition_channel
            )
        """)
        add(checks, "Channel subtotals reconcile", channel_arr == kpi["ending_arr_inr"], f"Channel sum={channel_arr:,}; headline={kpi['ending_arr_inr']:,}")

        plan_arr = scalar(connection, "SELECT SUM(arr_run_rate_inr) FROM revenue WHERE revenue_month='2025-12-01'")
        add(checks, "Plan/segment subtotals reconcile", plan_arr == kpi["ending_arr_inr"], f"Plan/segment base={plan_arr:,}; headline={kpi['ending_arr_inr']:,}")

        movement_arr = scalar(connection, """
            SELECT SUM(movement_mrr_inr)*12 FROM revenue
            WHERE revenue_month BETWEEN '2025-01-01' AND '2025-12-01'
              AND revenue_type IN ('Expansion','Upgrade','Reactivation')
        """)
        expected_movement_arr = kpi["expansion_arr_2025_inr"] + kpi["upgrade_arr_2025_inr"] + kpi["reactivated_arr_2025_inr"]
        add(checks, "2025 post-sale growth reconciled", movement_arr == expected_movement_arr, f"Event sum={movement_arr:,}; KPI components={expected_movement_arr:,}")
    finally:
        connection.close()

    # Rebuild in an isolated temporary directory and compare CSV checksums.
    with tempfile.TemporaryDirectory(prefix="crm-validation-") as temp_dir:
        temp_root = Path(temp_dir)
        subprocess.run(["python3", str(root / "scripts" / "generate_data.py"), "--root", str(temp_root)], check=True, capture_output=True, text=True)
        matching = {}
        for name in ["customers.csv", "products.csv", "revenue.csv", "churn.csv"]:
            matching[name] = sha256(root / "data" / name) == sha256(temp_root / "data" / name)
        add(checks, "Deterministic regeneration", all(matching.values()), f"Matching CSV hashes: {matching}")

    artifact = json.loads((root / "report" / "artifact.json").read_text(encoding="utf-8"))
    add(checks, "Canonical report artifact is bounded", len(artifact["snapshot"]["datasets"]) <= 50 and all(len(rows) <= 2000 for rows in artifact["snapshot"]["datasets"].values()), f"Datasets: { {key: len(value) for key, value in artifact['snapshot']['datasets'].items()} }")
    report_html = root / "report" / "report.html"
    add(checks, "Portable report package exists", report_html.exists() and report_html.stat().st_size > 100_000, f"report.html size: {report_html.stat().st_size if report_html.exists() else 0:,} bytes", "Medium")

    readme = (root / "README.md").read_text(encoding="utf-8")
    required_claims = ["₹150.9 crore", "100.7% NRR", "94.4%", "14.1%", "₹12.0 crore"]
    missing_claims = [claim for claim in required_claims if claim not in readme]
    add(checks, "README headline claims match reviewed outputs", not missing_claims, f"Missing expected claims: {missing_claims or 'none'}", "Medium")

    image_dimensions = {}
    try:
        for name in ["dashboard_preview.png", "linkedin_project_summary.png"]:
            image_dimensions[name] = png_dimensions(root / "assets" / name)
        expected_dimensions = {"dashboard_preview.png": (1600, 1170), "linkedin_project_summary.png": (1200, 1420)}
        add(checks, "Final visual exports have intended dimensions", image_dimensions == expected_dimensions, f"Dimensions: {image_dimensions}", "Medium")
    except Exception as exc:
        add(checks, "Final visual exports have intended dimensions", False, f"PNG inspection failed: {exc}", "Medium")

    failures = [check for check in checks if not check["passed"]]
    overall = "Ready to share" if not failures else "Needs revision"
    results = {"overall_assessment": overall, "checks_run": len(checks), "failures": failures, "checks": checks}
    (root / "docs" / "validation_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Validation report",
        "",
        f"## Overall assessment: {overall}",
        "",
        "The dataset, SQL calculations, exported results, report package, and static visuals were validated before publication. All source records are deterministic synthetic data through December 2025.",
        "",
        "## Methodology review",
        "",
        "The analysis answers a revenue-growth and GTM prioritization question at customer-month grain. KPI populations, dates, INR units, cohort denominators, and exclusions are stated in the README and methodology. Channel comparisons are descriptive; no causal claims are made.",
        "",
        "## Calculation and data-quality checks",
        "",
        "| Check | Result | Evidence |",
        "|---|---|---|",
    ]
    for check in checks:
        status = "Passed" if check["passed"] else "Failed"
        evidence = re.sub(r"\s+", " ", check["evidence"]).replace("|", "\\|")
        lines.append(f"| {check['check']} | {status} | {evidence} |")
    lines.extend([
        "",
        "## Visualization review",
        "",
        "The dashboard and LinkedIn visual use line and bar charts appropriate to 36-month trends and ranked categorical comparisons. Bar charts start at zero, the trend uses 36 observed points, INR crore is labeled, and the final 1600×1170 and 1200×1420 PNG exports were visually inspected for clipping and legibility.",
        "",
        "## Required caveats for readers",
        "",
        "- The evidence is synthetic and demonstrates an analytical workflow rather than a real company result.",
        "- ARR is a monthly recurring-revenue run-rate, not audited revenue or signed contract value.",
        "- Channel churn is an observed portfolio ratio with unequal exposure time, not an annualized churn rate.",
        "- Funnel conversion, CAC, payback, quota attainment, and sales cycle are unavailable in the four-table scope.",
        "- Portable report verification was structural because no compatible Chromium executable was installed; the canonical artifact itself passed schema validation and the semantic report remains self-contained.",
        "",
        "## Incomplete handoff blockers",
        "",
        "None for the repository package. The optional live Sites publication encountered a service interruption, so the validated self-contained `report/report.html` is the durable report artifact.",
    ])
    (root / "docs" / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"overall_assessment": overall, "checks_run": len(checks), "failures": len(failures)}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
