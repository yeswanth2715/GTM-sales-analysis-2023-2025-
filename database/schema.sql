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
