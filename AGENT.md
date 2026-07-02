# AGENT Guide - Lipa Polepole

This file is a developer-focused handoff for AI agents and engineers working on this repository.

## 1) Project Summary

Lipa Polepole is an installment tracking system for Kenyan small businesses:
- Vendors register/login and manage customers + installment plans.
- Vendors record manual payments.
- Customers use a public tracking link to view balance and pay via M-Pesa STK push.

## 2) Tech Stack

- **Backend**: FastAPI (CF Python Workers) + D1 (SQLite) + PyJWT
- **Frontend**: React (Vite) + Axios + React Router
- **Payments**: M-Pesa sandbox (Daraja API v2)
- **Infra**: Cloudflare Workers + D1 + Pages

## 3) Current Architecture

```
backend/
  src/
    main.py           — Worker entrypoint (LipaPolepole.fetch)
    app.py            — FastAPI app (module-level)
    api/v1/
      auth.py         — vendor register/login
      customers.py    — CRUD customers
      plans.py        — CRUD plans + public tracking
      payments.py     — CRUD payments
      og.py           — Open Graph meta page
    core/
      config.py       — Settings from env dict
      deps.py         — get_d1(), get_current_vendor()
      money.py        — float-cents conversion
      security.py     — JWT (PyJWT) + pbkdf2_sha256 hashing
    db/
      d1.py           — D1 query helper (minimal SQLite wrapper)
    schemas/          — Pydantic v2 request/response models
    services/         — (reserved for mpesa.py etc.)
  schema.sql          — D1 table DDL
  wrangler.jsonc      — CF Workers config
  pyproject.toml      — Python deps
frontend/
  src/
    pages/
      vendor/         — Dashboard, customers, plans
      customer/       — Public tracking (BalanceView)
    services/         — API calls (vendorService, paymentService)
```

## 4) Migration — PostgreSQL → D1 (Completed)

The app was fully migrated from PostgreSQL + SQLAlchemy to CF Workers + D1:

1. **D1 schema** — `schema.sql` with 4 tables (vendors, customers, installment_plans, payments). Money stored as INTEGER cents.
2. **D1 helper** — `src/db/d1.py`: minimal wrapper with `query()`, `query_one()`, `execute()`.
3. **Config** — `src/core/config.py`: class-based `Settings` initialized from env dict.
4. **Deps** — `src/core/deps.py`: `get_d1()` (injects DB binding from request scope), `get_current_vendor()` (JWT auth).
5. **Security** — `src/core/security.py`: PyJWT for tokens, `hashlib.pbkdf2_hmac('sha256')` for passwords. No C extensions needed (bcrypt/cryptography avoided).
6. **App** — `src/app.py`: module-level FastAPI with CORS + env injection middleware.
7. **Worker** — `src/main.py`: `LipaPolepole(WorkerEntryPoint)` injects `self.env` bindings into ASGI scope via `EnvInjector`.
8. **All 5 routers** rewritten for D1 — SQL queries replace SQLAlchemy ORM. Float KSh ↔ cents conversion at API boundary.
9. **wrangler.jsonc** — D1 binding (`DB`), Python Workers flag, dev vars.

## 5) Money Handling

- D1 stores amounts as **INTEGER cents** (e.g., `150000` = KSh 1,500.00)
- API boundary: `to_cents(ksh_float)` → `int` on input, `to_ksh(cents)` → `float` on output
- All SQL joins/aggregations use raw cents

## 6) Critical Rules

- Do not expose vendor-protected endpoints publicly.
- Public customer ops use `tracking_token`, not numeric plan IDs.
- M-Pesa phone format: `254[17]XXXXXXXX`.
- Payment amount must be positive and ≤ remaining balance.
- **No C extensions** — avoid bcrypt, cryptography, or anything that needs native compilation.

## 7) M-Pesa Flow

1. Customer opens `/track/:trackingToken`
2. Customer enters phone + amount → clicks Pay
3. Frontend calls `POST /api/v1/payments/mpesa/stk/{tracking_token}`
4. Backend sends STK push via Daraja API
5. Safaricom callback hits `/api/v1/payments/mpesa/callback`
6. Backend reconciles by `CheckoutRequestID`, records Payment, updates plan

(Current implementation uses `MPESA_MOCK_MODE` for local dev — set `"MPESA_MOCK_MODE": "true"` in wrangler.jsonc vars.)

## 8) Key Dependencies

| Package | Version | Notes |
|---------|---------|-------|
| fastapi | 0.115.6 | Web framework |
| pyjwt | 2.10.1 | JWT tokens (pure Python) |
| pydantic | 2.10.4 | Schema validation |
| pydantic-email-validator | 0.0.1 | Email validation |

No passlib, bcrypt, python-jose, cryptography, sqlalchemy, alembic, or psycopg2.

## 9) How to Work Safely

- Before changing payment/auth logic, read `src/api/v1/payments.py` and `src/api/v1/plans.py`.
- For UI changes, run frontend build after edits.
- Test locally with `npx wrangler dev` from `backend/`.
- For D1 schema changes: update `schema.sql` *and* create a migration in `migrations/`.
- Keep user-requested behavior stable: arbitrary payment amounts up to balance, quick amount chips, auto-refresh after STK.
