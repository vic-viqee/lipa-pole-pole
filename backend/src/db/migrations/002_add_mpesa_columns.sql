-- Migration 002: Add M-Pesa callback columns to payments table
-- Run: npx wrangler d1 execute lipa-polepole-db --file ./src/db/migrations/002_add_mpesa_columns.sql --remote

ALTER TABLE payments ADD COLUMN phone TEXT;
ALTER TABLE payments ADD COLUMN mpesa_receipt_number TEXT;
ALTER TABLE payments ADD COLUMN mpesa_result_code TEXT;
ALTER TABLE payments ADD COLUMN mpesa_result_desc TEXT;
