# Project Instructions

## Architecture & Conventions
- **Backend**: FastAPI with SQLAlchemy 2.0. Async session management is preferred where applicable.
- **Frontend**: React 19 with Vite. Use OKLCH colors and the custom design system in `frontend/src/components/ui/`.
- **Authentication**: JWT-based. `passlib` is used for password hashing.
- **Dependency Management**: Rigorously specify versions in `requirements.txt` to avoid library incompatibilities.
- **Public Tracking Page**: Uses `react-helmet-async` for dynamic meta tags. OG previews served via `GET /og/track/{token}` backend endpoint.
- **Public API**: `GET /plans/track/{token}` returns `PublicPlanResponse` which includes `vendor_name` and `customer_name` for personalized display.
- **Tracking Tokens**: Default length is `token_urlsafe(8)` (~11 chars). New plans get short tokens; existing tokens unchanged.

## Key Files
- `backend/app/schemas/plan.py` — `PublicPlanResponse` with vendor_name, customer_name
- `backend/app/api/v1/og.py` — Social sharing OG meta tag endpoint
- `frontend/src/pages/customer/BalanceView.jsx` — Public tracking page (personalized greeting, M-Pesa pay form, receipt timeline)
- `frontend/src/pages/vendor/PlanDetails.jsx` — Includes WhatsApp share + copy link

## Known Issues & Fixes
- **Bcrypt Compatibility**: Always use `bcrypt==3.2.0` with `passlib==1.7.4`. Newer versions of `bcrypt` (4.0+) break `passlib` due to the removal of `__about__` and changes in password length handling.
- **Tracking Token Change**: `token_urlsafe(16)` → `token_urlsafe(8)` only affects new plans. Run a one-off migration for existing plans if shorter tokens are needed.

## Workflows
- **Verification**: Always run `verify_fix.py` (or a similar script) after modifying authentication or core business logic to ensure E2E functionality.
- **Frontend Build**: Run `npm run build` in `frontend/` after UI changes.
