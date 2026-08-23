#!/usr/bin/env python3
"""Execute the portfolio SQL files and export reviewable result tables."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path


def write_csv(path: Path, columns: list[str], rows: list[sqlite3.Row]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows([tuple(row) for row in rows])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    database_path = root / "database" / "crm_growth.db"
    sql_dir = root / "sql"
    output_dir = root / "analysis" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    summary: dict[str, dict] = {}
    try:
        for sql_path in sorted(sql_dir.glob("*.sql")):
            query = sql_path.read_text(encoding="utf-8")
            cursor = connection.execute(query)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            output_path = output_dir / f"{sql_path.stem}.csv"
            write_csv(output_path, columns, rows)
            summary[sql_path.stem] = {
                "sql_file": str(sql_path.relative_to(root)),
                "output_file": str(output_path.relative_to(root)),
                "row_count": len(rows),
                "columns": columns,
            }

        quality_rows = connection.execute(
            (sql_dir / "01_data_quality.sql").read_text(encoding="utf-8")
        ).fetchall()
        failed_checks = [dict(row) for row in quality_rows if row["issue_count"] != 0]
        if failed_checks:
            raise RuntimeError(f"Data quality checks failed: {failed_checks}")

        kpi_row = connection.execute(
            (sql_dir / "02_executive_kpis.sql").read_text(encoding="utf-8")
        ).fetchone()
        metrics = dict(kpi_row)

        channels = [dict(row) for row in connection.execute(
            (sql_dir / "04_gtm_channel_performance.sql").read_text(encoding="utf-8")
        ).fetchall()]
        retention = [dict(row) for row in connection.execute(
            (sql_dir / "06_annual_retention.sql").read_text(encoding="utf-8")
        ).fetchall()]
        churn_reasons = [dict(row) for row in connection.execute(
            (sql_dir / "08_churn_reasons.sql").read_text(encoding="utf-8")
        ).fetchall()]

        metrics["top_channel_by_ending_arr"] = channels[0]["acquisition_channel"]
        metrics["top_channel_ending_arr_inr"] = channels[0]["ending_arr_inr"]
        metrics["lowest_churn_channel"] = min(channels, key=lambda row: row["observed_logo_churn_pct"])["acquisition_channel"]
        metrics["highest_churn_channel"] = max(channels, key=lambda row: row["observed_logo_churn_pct"])["acquisition_channel"]
        metrics["nrr_2024_pct"] = retention[0]["nrr_pct"]
        metrics["top_churn_reason"] = churn_reasons[0]["churn_reason"]
        metrics["top_churn_reason_arr_lost_inr"] = churn_reasons[0]["arr_lost_inr"]

        (output_dir / "headline_metrics.json").write_text(
            json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
        )
        (output_dir / "run_manifest.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        connection.close()

    print(json.dumps({"status": "passed", "queries": len(summary), "metrics": metrics}, indent=2))


if __name__ == "__main__":
    main()
