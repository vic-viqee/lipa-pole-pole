# Lipa Pole Pole

Installment payment tracking for Kenyan small businesses with M-Pesa integration.

## Live Demo

- **Tracking Page**: [https://lipa-polepole-api.victorlewismurimi.workers.dev/track/ClaWVn4kucE](https://lipa-polepole-api.victorlewismurimi.workers.dev/track/ClaWVn4kucE)

## About

Lipa Pole Pole ("pay slowly" in Swahili) helps small businesses manage installment payments. Vendors create payment plans for customers, who get a shareable tracking link to view their balance, payment history, and pay via M-Pesa STK Push — no login required. The tracking page includes WhatsApp-friendly OG meta tags for rich previews when shared.

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
