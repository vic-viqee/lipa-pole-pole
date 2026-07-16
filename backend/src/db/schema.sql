-- Lipa Polepole D1 Schema (SQLite)
-- Money stored as INTEGER cents to avoid float precision issues.
-- All TIMESTAMPs stored as TEXT in ISO 8601 format.

CREATE TABLE IF NOT EXISTS vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_vendors_email ON vendors(email);
CREATE INDEX IF NOT EXISTS idx_vendors_phone ON vendors(phone);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    national_id TEXT NOT NULL,
    vendor_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);

CREATE INDEX IF NOT EXISTS idx_customers_vendor_id ON customers(vendor_id);

CREATE TABLE IF NOT EXISTS installment_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    total_price INTEGER NOT NULL,
    deposit_paid INTEGER NOT NULL,
    amount_paid INTEGER NOT NULL DEFAULT 0,
    customer_id INTEGER NOT NULL,
    vendor_id INTEGER NOT NULL,
    tracking_token TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'completed', 'defaulted')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);

CREATE INDEX IF NOT EXISTS idx_plans_vendor_id ON installment_plans(vendor_id);
CREATE INDEX IF NOT EXISTS idx_plans_customer_id ON installment_plans(customer_id);
CREATE INDEX IF NOT EXISTS idx_plans_tracking_token ON installment_plans(tracking_token);
CREATE INDEX IF NOT EXISTS idx_plans_status ON installment_plans(status);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount INTEGER NOT NULL,
    mpesa_transaction_id TEXT,
    plan_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES installment_plans(id)
);

CREATE INDEX IF NOT EXISTS idx_payments_plan_id ON payments(plan_id);
CREATE INDEX IF NOT EXISTS idx_payments_mpesa_txn ON payments(mpesa_transaction_id);

CREATE TABLE IF NOT EXISTS mpesa_stk_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checkout_request_id TEXT NOT NULL UNIQUE,
    merchant_request_id TEXT,
    plan_id INTEGER NOT NULL,
    phone TEXT NOT NULL,
    requested_amount INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    processed_at TEXT,
    FOREIGN KEY (plan_id) REFERENCES installment_plans(id)
);

CREATE INDEX IF NOT EXISTS idx_stk_checkout_request ON mpesa_stk_requests(checkout_request_id);
CREATE INDEX IF NOT EXISTS idx_stk_plan_id ON mpesa_stk_requests(plan_id);
