#!/usr/bin/env python3
"""Generate a deterministic synthetic B2B SaaS CRM dataset.

The project intentionally uses only Python's standard library so that the full
portfolio can be reproduced without installing packages.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sqlite3
from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from pathlib import Path


SEED = 20260823
ANALYSIS_START = date(2023, 1, 1)
ANALYSIS_END = date(2025, 12, 1)


def month_add(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    return date(month_index // 12, month_index % 12 + 1, 1)


def month_diff(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + end.month - start.month


def month_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current = month_add(current, 1)


def iso_month(value: date) -> str:
    return value.isoformat()


def stable_choice(rng: random.Random, values: list[str], weights: list[float]) -> str:
    return rng.choices(values, weights=weights, k=1)[0]


@dataclass
class CustomerPlan:
    customer_id: str
    contract_month: date
    initial_product_id: str
    initial_mrr: int
    channel: str
    segment: str
    churn_month: date | None
    churn_reason: str | None
    pause_start: date | None
    reactivation_month: date | None
    upgrade_month: date | None
    expansion_months: list[date]


PRODUCTS = [
    {
        "product_id": "P001",
        "product_name": "Professional CRM",
        "plan_tier": "Professional",
        "billing_frequency": "Annual",
        "included_users": 75,
        "base_monthly_price_inr": 90000,
        "target_segment": "Mid-Market",
    },
    {
        "product_id": "P002",
        "product_name": "Enterprise CRM",
        "plan_tier": "Enterprise",
        "billing_frequency": "Annual",
        "included_users": 250,
        "base_monthly_price_inr": 250000,
        "target_segment": "Large Enterprise",
    },
]


def company_name(index: int, rng: random.Random) -> str:
    prefixes = [
        "Aarav", "BluePeak", "Cobalt", "DigiCore", "Everstone", "FinAxis",
        "Greenline", "HexaWorks", "Indus", "Jupiter", "KiteBridge", "Lumina",
        "Meridian", "Nexora", "Orbit", "PrimeArc", "Quantara", "Riverbend",
        "SkyGrid", "TrueNorth", "UrbanStack", "Vertex", "Westlake", "Zenith",
    ]
    suffixes = [
        "Systems", "Services", "Solutions", "Technologies", "Networks",
        "Consulting", "Industries", "Enterprises", "Labs", "Digital",
    ]
    return f"{rng.choice(prefixes)} {rng.choice(suffixes)} {index:03d}"


def create_customer(
    index: int,
    contract_month: date,
    rng: random.Random,
) -> tuple[dict, CustomerPlan]:
    month_number = month_diff(ANALYSIS_START, contract_month)
    enterprise_share = min(0.58, 0.34 + max(month_number, 0) * 0.006)
    initial_product_id = "P002" if rng.random() < enterprise_share else "P001"
    segment = "Large Enterprise" if initial_product_id == "P002" else "Mid-Market"

    channels = ["Partner", "Outbound", "Inbound", "Events", "Referral"]
    if initial_product_id == "P002":
        weights = [0.29, 0.26, 0.14, 0.23, 0.08]
    else:
        weights = [0.19, 0.31, 0.29, 0.09, 0.12]
    channel = stable_choice(rng, channels, weights)

    sales_owner_by_channel = {
        "Partner": ["Aditi Rao", "Vikram Shah", "Meera Iyer"],
        "Outbound": ["Rahul Mehta", "Neha Kapoor", "Arjun Nair"],
        "Inbound": ["Sara Khan", "Neha Kapoor", "Aditi Rao"],
        "Events": ["Vikram Shah", "Meera Iyer", "Arjun Nair"],
        "Referral": ["Sara Khan", "Aditi Rao", "Meera Iyer"],
    }
    owner = rng.choice(sales_owner_by_channel[channel])

    industries = [
        "IT Services", "Financial Services", "Healthcare", "Manufacturing",
        "Retail", "Professional Services",
    ]
    industry_weights = [0.24, 0.19, 0.12, 0.19, 0.12, 0.14]
    regions = ["North", "South", "West", "East", "Central"]
    region_weights = [0.22, 0.28, 0.30, 0.13, 0.07]

    if initial_product_id == "P001":
        initial_mrr = rng.randrange(90000, 171000, 5000)
    else:
        initial_mrr = rng.randrange(250000, 501000, 10000)

    months_observable = month_diff(contract_month, ANALYSIS_END)
    eligible_months = max(0, months_observable)

    # Channel and plan effects make the synthetic GTM story realistic but not perfect.
    churn_probability = {
        "Partner": 0.075,
        "Outbound": 0.145,
        "Inbound": 0.115,
        "Events": 0.095,
        "Referral": 0.065,
    }[channel]
    if initial_product_id == "P002":
        churn_probability -= 0.025

    churn_month = None
    churn_reason = None
    if eligible_months >= 10 and rng.random() < churn_probability:
        tenure = rng.randint(9, min(30, eligible_months))
        churn_month = month_add(contract_month, tenure)
        reason_weights = {
            "Partner": [0.22, 0.24, 0.22, 0.22, 0.10],
            "Outbound": [0.29, 0.20, 0.24, 0.12, 0.15],
            "Inbound": [0.25, 0.27, 0.22, 0.13, 0.13],
            "Events": [0.17, 0.25, 0.18, 0.25, 0.15],
            "Referral": [0.20, 0.20, 0.24, 0.26, 0.10],
        }[channel]
        churn_reason = stable_choice(
            rng,
            ["Budget Cuts", "Missing Integration", "Low Adoption", "Vendor Consolidation", "Implementation Complexity"],
            reason_weights,
        )

    # Reactivation is a temporary suspension, never a permanent churn record.
    pause_start = None
    reactivation_month = None
    if churn_month is None and eligible_months >= 14 and rng.random() < 0.075:
        pause_tenure = rng.randint(8, min(22, eligible_months - 4))
        pause_start = month_add(contract_month, pause_tenure)
        reactivation_month = month_add(pause_start, rng.randint(2, 4))

    upgrade_month = None
    if initial_product_id == "P001" and eligible_months >= 13 and rng.random() < 0.27:
        upgrade_tenure = rng.randint(11, min(25, eligible_months))
        candidate = month_add(contract_month, upgrade_tenure)
        if churn_month is None or candidate < churn_month:
            if pause_start is None or not (pause_start <= candidate < reactivation_month):
                upgrade_month = candidate

    expansion_months: list[date] = []
    if eligible_months >= 9 and rng.random() < (0.42 if initial_product_id == "P002" else 0.31):
        first_tenure = rng.randint(7, min(20, eligible_months))
        candidate = month_add(contract_month, first_tenure)
        if (churn_month is None or candidate < churn_month) and candidate != upgrade_month:
            if pause_start is None or not (pause_start <= candidate < reactivation_month):
                expansion_months.append(candidate)
    if eligible_months >= 22 and rng.random() < 0.18:
        candidate = month_add(contract_month, rng.randint(18, min(31, eligible_months)))
        if (churn_month is None or candidate < churn_month) and candidate != upgrade_month:
            if pause_start is None or not (pause_start <= candidate < reactivation_month):
                if candidate not in expansion_months:
                    expansion_months.append(candidate)
    expansion_months.sort()

    customer_id = f"C{index:04d}"
    customer = {
        "customer_id": customer_id,
        "company_name": company_name(index, rng),
        "industry": stable_choice(rng, industries, industry_weights),
        "company_segment": segment,
        "region": stable_choice(rng, regions, region_weights),
        "acquisition_channel": channel,
        "sales_owner": owner,
        "signup_date": (contract_month.replace(day=max(1, rng.randint(1, 20))) if contract_month >= date(2023, 1, 1) else contract_month).isoformat(),
        "first_contract_date": contract_month.isoformat(),
        "initial_product_id": initial_product_id,
        "current_product_id": "P002" if upgrade_month and upgrade_month <= ANALYSIS_END else initial_product_id,
        "lifecycle_status": "Churned" if churn_month and churn_month <= ANALYSIS_END else "Active",
    }
    plan = CustomerPlan(
        customer_id=customer_id,
        contract_month=contract_month,
        initial_product_id=initial_product_id,
        initial_mrr=initial_mrr,
        channel=channel,
        segment=segment,
        churn_month=churn_month,
        churn_reason=churn_reason,
        pause_start=pause_start,
        reactivation_month=reactivation_month,
        upgrade_month=upgrade_month,
        expansion_months=expansion_months,
    )
    return customer, plan


def generate_rows() -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    rng = random.Random(SEED)
    customers: list[dict] = []
    plans: list[CustomerPlan] = []
    index = 1

    # Opening cohort: contracts signed during 2022 and active at the analysis start.
    for _ in range(96):
        contract_month = month_add(date(2022, 1, 1), rng.randint(0, 11))
        customer, plan = create_customer(index, contract_month, rng)
        customers.append(customer)
        plans.append(plan)
        index += 1

    # New-logo volume rises gradually and includes realistic seasonality.
    for month_index, contract_month in enumerate(month_range(ANALYSIS_START, ANALYSIS_END)):
        seasonal = {1: -2, 3: 2, 6: 1, 9: 2, 10: 1, 12: -1}.get(contract_month.month, 0)
        count = 10 + month_index // 8 + seasonal
        for _ in range(max(7, count)):
            customer, plan = create_customer(index, contract_month, rng)
            customers.append(customer)
            plans.append(plan)
            index += 1

    revenue: list[dict] = []
    churn: list[dict] = []
    revenue_id = 1
    churn_id = 1

    for plan in plans:
        current_product = plan.initial_product_id
        current_mrr = plan.initial_mrr

        for month in month_range(max(plan.contract_month, ANALYSIS_START), ANALYSIS_END):
            if plan.churn_month and month >= plan.churn_month:
                break
            if plan.pause_start and plan.reactivation_month and plan.pause_start <= month < plan.reactivation_month:
                continue

            opening_mrr = current_mrr
            movement = 0
            revenue_type = "Recurring"

            if month == plan.contract_month and plan.contract_month >= ANALYSIS_START:
                opening_mrr = 0
                movement = current_mrr
                revenue_type = "New"
            elif plan.reactivation_month and month == plan.reactivation_month:
                opening_mrr = 0
                movement = current_mrr
                revenue_type = "Reactivation"
            elif plan.upgrade_month and month == plan.upgrade_month:
                old_mrr = current_mrr
                current_product = "P002"
                current_mrr = max(250000, int(round(old_mrr * rng.uniform(1.55, 2.05) / 5000) * 5000))
                movement = current_mrr - old_mrr
                revenue_type = "Upgrade"
            elif month in plan.expansion_months:
                old_mrr = current_mrr
                current_mrr = int(round(old_mrr * rng.uniform(1.07, 1.19) / 5000) * 5000)
                movement = current_mrr - old_mrr
                revenue_type = "Expansion"

            revenue.append(
                {
                    "revenue_id": f"R{revenue_id:06d}",
                    "revenue_month": iso_month(month),
                    "customer_id": plan.customer_id,
                    "product_id": current_product,
                    "revenue_type": revenue_type,
                    "opening_mrr_inr": opening_mrr,
                    "movement_mrr_inr": movement,
                    "closing_mrr_inr": current_mrr,
                    "recognized_revenue_inr": current_mrr,
                    "arr_run_rate_inr": current_mrr * 12,
                }
            )
            revenue_id += 1

        if plan.churn_month and plan.churn_month <= ANALYSIS_END:
            churn_date = plan.churn_month.replace(day=min(15, monthrange(plan.churn_month.year, plan.churn_month.month)[1]))
            churn.append(
                {
                    "churn_id": f"CH{churn_id:04d}",
                    "customer_id": plan.customer_id,
                    "product_id": current_product,
                    "churn_date": churn_date.isoformat(),
                    "churn_reason": plan.churn_reason,
                    "mrr_lost_inr": current_mrr,
                    "tenure_months": month_diff(plan.contract_month, plan.churn_month),
                }
            )
            churn_id += 1

    return customers, PRODUCTS, revenue, churn


TABLE_COLUMNS = {
    "customers": [
        "customer_id", "company_name", "industry", "company_segment", "region",
        "acquisition_channel", "sales_owner", "signup_date", "first_contract_date",
        "initial_product_id", "current_product_id", "lifecycle_status",
    ],
    "products": [
        "product_id", "product_name", "plan_tier", "billing_frequency",
        "included_users", "base_monthly_price_inr", "target_segment",
    ],
    "revenue": [
        "revenue_id", "revenue_month", "customer_id", "product_id", "revenue_type",
        "opening_mrr_inr", "movement_mrr_inr", "closing_mrr_inr",
        "recognized_revenue_inr", "arr_run_rate_inr",
    ],
    "churn": [
        "churn_id", "customer_id", "product_id", "churn_date", "churn_reason",
        "mrr_lost_inr", "tenure_months",
    ],
}


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS churn;
DROP TABLE IF EXISTS revenue;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    plan_tier TEXT NOT NULL CHECK (plan_tier IN ('Professional', 'Enterprise')),
    billing_frequency TEXT NOT NULL,
    included_users INTEGER NOT NULL,
    base_monthly_price_inr INTEGER NOT NULL CHECK (base_monthly_price_inr > 0),
    target_segment TEXT NOT NULL
);

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    industry TEXT NOT NULL,
    company_segment TEXT NOT NULL CHECK (company_segment IN ('Mid-Market', 'Large Enterprise')),
    region TEXT NOT NULL,
    acquisition_channel TEXT NOT NULL,
    sales_owner TEXT NOT NULL,
    signup_date TEXT NOT NULL,
    first_contract_date TEXT NOT NULL,
    initial_product_id TEXT NOT NULL REFERENCES products(product_id),
    current_product_id TEXT NOT NULL REFERENCES products(product_id),
    lifecycle_status TEXT NOT NULL CHECK (lifecycle_status IN ('Active', 'Churned'))
);

CREATE TABLE revenue (
    revenue_id TEXT PRIMARY KEY,
    revenue_month TEXT NOT NULL,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    product_id TEXT NOT NULL REFERENCES products(product_id),
    revenue_type TEXT NOT NULL CHECK (revenue_type IN ('New', 'Recurring', 'Expansion', 'Upgrade', 'Reactivation')),
    opening_mrr_inr INTEGER NOT NULL CHECK (opening_mrr_inr >= 0),
    movement_mrr_inr INTEGER NOT NULL CHECK (movement_mrr_inr >= 0),
    closing_mrr_inr INTEGER NOT NULL CHECK (closing_mrr_inr > 0),
    recognized_revenue_inr INTEGER NOT NULL CHECK (recognized_revenue_inr > 0),
    arr_run_rate_inr INTEGER NOT NULL CHECK (arr_run_rate_inr = closing_mrr_inr * 12),
    UNIQUE (revenue_month, customer_id)
);

CREATE TABLE churn (
    churn_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL UNIQUE REFERENCES customers(customer_id),
    product_id TEXT NOT NULL REFERENCES products(product_id),
    churn_date TEXT NOT NULL,
    churn_reason TEXT NOT NULL,
    mrr_lost_inr INTEGER NOT NULL CHECK (mrr_lost_inr > 0),
    tenure_months INTEGER NOT NULL CHECK (tenure_months > 0)
);

CREATE INDEX idx_revenue_month ON revenue(revenue_month);
CREATE INDEX idx_revenue_customer ON revenue(customer_id);
CREATE INDEX idx_revenue_product ON revenue(product_id);
CREATE INDEX idx_customers_channel ON customers(acquisition_channel);
CREATE INDEX idx_customers_owner ON customers(sales_owner);
CREATE INDEX idx_churn_date ON churn(churn_date);
""".strip()


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_database(path: Path, customers: list[dict], products: list[dict], revenue: list[dict], churn: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        connection.executescript(SCHEMA_SQL)
        for table_name, rows in [
            ("products", products),
            ("customers", customers),
            ("revenue", revenue),
            ("churn", churn),
        ]:
            columns = TABLE_COLUMNS[table_name]
            placeholders = ", ".join("?" for _ in columns)
            connection.executemany(
                f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})",
                [[row[column] for column in columns] for row in rows],
            )
        connection.commit()
        result = connection.execute("PRAGMA foreign_key_check").fetchall()
        if result:
            raise RuntimeError(f"Foreign key validation failed: {result[:5]}")
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    data_dir = root / "data"
    database_dir = root / "database"
    metadata_dir = root / "analysis" / "outputs"
    data_dir.mkdir(parents=True, exist_ok=True)
    database_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    customers, products, revenue, churn = generate_rows()
    for table_name, rows in [
        ("customers", customers),
        ("products", products),
        ("revenue", revenue),
        ("churn", churn),
    ]:
        write_csv(data_dir / f"{table_name}.csv", rows, TABLE_COLUMNS[table_name])

    (database_dir / "schema.sql").write_text(SCHEMA_SQL + "\n", encoding="utf-8")
    create_database(database_dir / "crm_growth.db", customers, products, revenue, churn)

    metadata = {
        "synthetic": True,
        "seed": SEED,
        "analysis_start": ANALYSIS_START.isoformat(),
        "analysis_end": ANALYSIS_END.isoformat(),
        "currency": "INR",
        "row_counts": {
            "customers": len(customers),
            "products": len(products),
            "revenue": len(revenue),
            "churn": len(churn),
        },
    }
    (metadata_dir / "generation_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
