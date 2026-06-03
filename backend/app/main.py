from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.bootstrap import ensure_database_schema
from app.models import vendor, customer, plan, payment, mpesa_request
from app.api.v1 import auth, customers, plans, payments, og

ensure_database_schema()

app = FastAPI(title="Lipa Polepole API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(plans.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(og.router)

@app.get("/")
def root():
    return {"message": "Lipa Polepole API is running"}
