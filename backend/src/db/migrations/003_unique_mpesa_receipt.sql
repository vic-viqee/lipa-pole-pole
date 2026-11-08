-- Migration 003: Enforce uniqueness on M-Pesa receipt numbers
-- Prevents duplicate payment records from replayed callbacks or data races.
-- Partial index allows multiple NULLs (pending/manual rows without a receipt).
-- Run: npx wrangler d1 execute lipa-polepole-db --file ./src/db/migrations/003_unique_mpesa_receipt.sql --remote

CREATE UNIQUE INDEX IF NOT EXISTS idx_payments_mpesa_receipt_unique
    ON payments(mpesa_receipt_number)
    WHERE mpesa_receipt_number IS NOT NULL;
