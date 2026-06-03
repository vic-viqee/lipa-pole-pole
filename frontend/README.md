# Lipa Pole Pole

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-19-61dafb.svg" alt="React">
  <img src="https://img.shields.io/badge/M--Pesa-Sandbox-orange.svg" alt="M-Pesa">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

> **Lipa Pole Pole** (Swahili for "Pay Slowly Slowly") is an installment management platform designed for small businesses in Kenya. Track customer payments, manage installment plans, and accept M-Pesa mobile money payments — all in one place.

---

## What It Does

### For Vendors
- Create and manage customer accounts
- Set up installment plans with total price and initial deposits
- Track payment progress in real-time
- Record payments manually or let customers pay via M-Pesa
- Share tracking links with customers so they can monitor their balance

### For Customers
- View their current balance and payment history
- Make M-Pesa payments directly from their phone
- Track progress toward completing their installment plan

---

## Key Features

| Feature | Description |
|---------|-------------|
| **M-Pesa Integration** | Real-time STK Push payments via Safaricom API |
| **Public Tracking Pages** | Shareable links let customers track their balance without logging in |
| **Secure Authentication** | JWT-based auth with bcrypt password hashing |
| **Responsive Design** | Mobile-first UI that works on any device |
| **Decimal-Safe** | All monetary calculations use proper decimal handling |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (or use SQLite for local dev)
- ngrok (for M-Pesa callbacks during development)

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your credentials
cp .env.example .env  # Edit .env with your values

# Start the server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open `http://localhost:5173` in your browser.

### M-Pesa Testing

1. Start ngrok: `ngrok http 8000`
2. Update `MPESA_CALLBACK_URL` in `.env` with your ngrok URL
3. Restart the backend
4. Use phone numbers starting with `254` (e.g., `254712345678`)

---

## Project Structure

```
lipa-pole-pole/
├── backend/
│   └── app/
│       ├── api/v1/        # API routes
│       ├── core/          # Config, security
│       ├── models/        # SQLAlchemy models
│       ├── schemas/        # Pydantic schemas
│       └── services/      # Business logic
├── frontend/
│   └── src/
│       ├── components/    # Reusable UI components
│       ├── context/       # React context providers
│       ├── pages/         # Page components
│       ├── services/      # API service layer
│       └── styles/        # Design system
└── README.md
```

---

## Tech Stack

**Backend**
- FastAPI — Modern Python web framework
- SQLAlchemy — Database ORM
- Pydantic v2 — Data validation
- python-jose — JWT authentication
- Safaricom M-Pesa API — Mobile money payments

**Frontend**
- React 19 — UI library
- Vite — Build tool
- React Router — Client-side routing
- Axios — HTTP client

**Database**
- PostgreSQL (production)
- SQLite (local development)

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL or SQLite connection string |
| `SECRET_KEY` | JWT signing secret |
| `MPESA_CONSUMER_KEY` | Safaricom API key |
| `MPESA_CONSUMER_SECRET` | Safaricom API secret |
| `MPESA_SHORTCODE` | Business shortcode |
| `MPESA_PASSKEY` | M-Pesa passkey |
| `MPESA_CALLBACK_URL` | HTTPS callback URL for M-Pesa |

See `.env.example` for a complete template.

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` — Register new vendor
- `POST /api/v1/auth/login` — Login and get JWT token

### Customers (Vendor only)
- `GET /api/v1/customers/` — List all customers
- `POST /api/v1/customers/` — Create customer
- `GET /api/v1/customers/{id}` — Get customer details

### Plans (Vendor only)
- `GET /api/v1/plans/` — List all plans
- `POST /api/v1/plans/` — Create installment plan
- `GET /api/v1/plans/{id}` — Get plan details

### Payments
- `POST /api/v1/payments/` — Record manual payment (vendor)
- `GET /api/v1/payments/plan/{id}` — Get payments for plan (vendor)
- `POST /api/v1/payments/mpesa/stk/{tracking_token}` — Initiate M-Pesa payment (public)
- `GET /api/v1/plans/track/{tracking_token}` — Get plan balance (public)
- `GET /api/v1/payments/public/{tracking_token}` — Get payment history (public)

Full API documentation available at `/docs` when the backend is running.

---

## Design System

The frontend uses a custom design system for consistency:

- **Colors**: OKLCH color space with M-Pesa green accent
- **Typography**: Syne (headings) + Plus Jakarta Sans (body)
- **Components**: Reusable Button, Input, Card, Badge, Progress

---

## Troubleshooting

**M-Pesa not working?**
- Ensure ngrok is running and `MPESA_CALLBACK_URL` is set correctly
- Verify HTTPS is enabled on your callback URL

**Login fails?**
- Check that `SECRET_KEY` matches between environments
- Ensure the database is accessible

**Database errors?**
- SQLite: Delete `test.db` and restart
- PostgreSQL: Verify user permissions

---

## License

MIT License — free to use and modify.
