-- Migration 004: Record which vendor recorded a manual payment
-- Manual/vendor-recorded payments store the acting vendor id; M-Pesa callback rows leave it NULL.
-- Run: npx wrangler d1 execute lipa-polepole-db --file ./src/db/migrations/004_manual_payment_audit.sql --remote

ALTER TABLE payments ADD COLUMN recorded_by_vendor_id INTEGER REFERENCES vendors(id);
CREATE INDEX IF NOT EXISTS idx_payments_recorded_by_vendor ON payments(recorded_by_vendor_id);
