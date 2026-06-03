# Lipa Pole Pole

Installment payment tracking for Kenyan small businesses with M-Pesa integration.

## Architecture

```
backend/   — FastAPI + SQLAlchemy + PostgreSQL
frontend/  — React + Vite
```

### Backend

- FastAPI with async SQLAlchemy 2.0
- Pydantic v2 schemas
- M-Pesa STK Push (Daraja API v2)
- JWT auth (vendor login)
- Public tracking page with OG meta tags (WhatsApp preview)

### Frontend

- React 18 + React Router 6
- react-helmet-async for dynamic head tags
- Responsive, mobile-first design
- Vendor dashboard + public customer tracking page

## Quick Start

```bash
# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Public Tracking

Each plan generates a short tracking token. Customers visit:

```
GET /track/{tracking_token}
```

The page shows their balance, payment history, and an M-Pesa payment form — no login required. Vendors can share the link via WhatsApp for a rich preview.

## License

MIT
