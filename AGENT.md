# AGENT Guide - Lipa Polepole

This file is a developer-focused handoff for AI agents and engineers working on this repository.

## 1) Project Summary

Lipa Polepole is an installment tracking system for small businesses:
- Vendors register/login and manage customers + installment plans.
- Vendors record manual payments.
- Customers use a public tracking link to view balance and pay via M-Pesa STK push.

## 2) Tech Stack

- Backend:
  - FastAPI
  - SQLAlchemy ORM
  - Pydantic v2
  - JWT auth (`python-jose`)
  - Password hashing (`passlib`)
- Frontend:
  - React (Vite)
  - Axios
  - React Router
- Payments:
  - M-Pesa sandbox integration via HTTP APIs

## 3) Current Architecture

- Backend app entry:
  - `backend/app/main.py`
- API routers:
  - `backend/app/api/v1/auth.py`
  - `backend/app/api/v1/customers.py`
  - `backend/app/api/v1/plans.py`
  - `backend/app/api/v1/payments.py`
- Models:
  - `Vendor`, `Customer`, `InstallmentPlan`, `Payment`, `MpesaStkRequest`
- Frontend routes:
  - Vendor: dashboard, customers, add customer/plan, plan details
  - Public: customer tracking page at `/track/:trackingToken`

## 4) Important Functional Changes Already Implemented

1. Fixed broken frontend Vite config (duplicate exports/imports).
2. Public tracking page now uses public payments endpoint.
3. M-Pesa callback hardened:
   - Persists `CheckoutRequestID` mapping (`MpesaStkRequest`)
   - Adds callback idempotency handling
4. Replaced public sequential plan IDs with `tracking_token` flow for:
   - Public plan fetch
   - Public payments fetch
   - Public STK initiation
5. Fixed registration password input binding bug.
6. Money fields switched from float to numeric/decimal handling.
7. Added stronger input validation for plan/payment amounts.
8. Replaced stub customers page with a functional listing view.
9. Added backend schema bootstrap for legacy DBs missing `tracking_token`.
10. Added customer-side M-Pesa pay form on tracking page.
11. Added quick amount buttons (`100`, `500`, `1000`, `Max`).
12. Added phone validation requiring `2541...` or `2547...`.
13. Added auto-refresh polling after STK push on tracking page.

## 5) Critical Rules and Constraints

- Do not expose vendor-protected endpoints publicly.
- Public customer operations must use `tracking_token`, not numeric plan IDs.
- M-Pesa phone format is enforced as `254[17]XXXXXXXX`.
- Payment amount must be positive and cannot exceed remaining balance.
- Money should stay in decimal-safe flow in backend.
- Do not run destructive git commands unless explicitly requested.

## 6) Database Notes

- `InstallmentPlan` includes `tracking_token` (unique, indexed).
- `MpesaStkRequest` table stores STK request/callback correlation.
- Startup bootstrap (`backend/app/db/bootstrap.py`) patches legacy schema by adding `tracking_token` when missing.

## 7) M-Pesa Flow (Current)

1. Customer opens tracking page (`/track/:trackingToken`).
2. Customer enters phone + amount and clicks Pay.
3. Frontend calls `POST /api/v1/payments/mpesa/stk/{tracking_token}`.
4. Backend sends STK push and stores `MpesaStkRequest`.
5. Safaricom callback hits `/api/v1/payments/mpesa/callback`.
6. Backend reconciles by `CheckoutRequestID`, records `Payment`, updates plan status/balance.

## 8) Recent Improvements — Tracking Page Makeover

1. **Vendor & Customer Names on Public Page**:
   - Backend `PublicPlanResponse` schema adds `vendor_name` + `customer_name` fields.
   - `GET /plans/track/{token}` now joins Vendor/Customer tables to return names.
   - Customer sees a personalized greeting (`"Hi {firstName}"`) with vendor's shop name in header.

2. **Shortened Tracking Tokens**:
   - Model default changed from `token_urlsafe(16)` → `token_urlsafe(8)` (~11 chars instead of 22).
   - Applies to new plans only; existing plans retain their longer tokens.

3. **Social Sharing (OG Meta Tags)**:
   - New backend endpoint `GET /og/track/{tracking_token}` serves an HTML page with Open Graph tags (title, description, URL) for WhatsApp/Facebook/Twitter crawlers.
   - The page instantly redirects to the SPA tracking page.
   - PlanDetails vendor panel now has a **"Share via WhatsApp"** button using the OG URL.

4. **Polished Public Tracking Page**:
   - Uses `react-helmet-async` for dynamic `<title>` and OG meta tags in the browser.
   - revamped payment form with phone icon, KSh prefix, inline validation, and cleaner messages.
   - Receipt-style timeline for payment history with timestamps and running totals.
   - Better loading skeletons, error states, and responsive design improvements.

## 10) Known Risks / Follow-Ups

- No formal migration system usage in this flow yet (bootstrap helps but Alembic migrations are still recommended).
- Callback security verification/signature validation can be improved.
- API and UI automated tests are minimal and should be expanded.
- Styling is mostly component-local CSS blocks; can be refactored for maintainability.

## 11) How to Work Safely as an Agent

- Before changing payment/auth logic, read:
  - `backend/app/api/v1/payments.py`
  - `backend/app/api/v1/plans.py`
  - `frontend/src/pages/customer/BalanceView.jsx`
  - `frontend/src/services/paymentService.js`
- For UI changes, run frontend build after edits.
- For backend edits, at minimum run compile checks.
- Keep user-requested behavior stable:
  - Customer can pay arbitrary amount up to balance
  - Quick amount chips exist
  - Status auto-refresh occurs after STK submission
