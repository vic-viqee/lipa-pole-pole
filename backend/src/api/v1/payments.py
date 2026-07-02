from fastapi import APIRouter, Depends, HTTPException

from src.core.deps import get_current_vendor, get_d1
from src.core.money import to_cents, to_ksh
from src.db.d1 import D1
from src.schemas.payment import PaymentCreate, PaymentResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse)
def init_payment(
    payment_data: PaymentCreate,
    d1: D1 = Depends(get_d1),
    current_vendor: dict = Depends(get_current_vendor),
):
    plan = d1.query_one(
        "SELECT * FROM installment_plans WHERE id = ? AND vendor_id = ?",
        payment_data.plan_id,
        current_vendor["id"],
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan["status"] != "active":
        raise HTTPException(status_code=400, detail="Plan is not active")

    amount_cents = to_cents(payment_data.amount)
    remaining = plan["total_price"] - plan["deposit_paid"] - plan["amount_paid"]
    if amount_cents > remaining:
        raise HTTPException(
            status_code=400,
            detail=f"Amount exceeds remaining balance of {to_ksh(remaining)}",
        )

    d1.execute(
        "INSERT INTO payments (amount, plan_id, status) VALUES (?, ?, 'pending')",
        amount_cents,
        payment_data.plan_id,
    )

    payment = d1.query_one(
        "SELECT id, amount, mpesa_transaction_id, plan_id, created_at "
        "FROM payments WHERE id = last_insert_rowid()"
    )
    if not payment:
        raise HTTPException(status_code=500, detail="Failed to create payment")

    return {
        "id": payment["id"],
        "amount": to_ksh(payment["amount"]),
        "mpesa_transaction_id": payment["mpesa_transaction_id"],
        "plan_id": payment["plan_id"],
        "created_at": payment["created_at"],
    }


@router.get("/", response_model=list[PaymentResponse])
def get_payments(
    d1: D1 = Depends(get_d1),
    current_vendor: dict = Depends(get_current_vendor),
):
    rows = d1.query(
        "SELECT p.id, p.amount, p.mpesa_transaction_id, p.plan_id, p.created_at "
        "FROM payments p "
        "JOIN installment_plans ip ON ip.id = p.plan_id "
        "WHERE ip.vendor_id = ? "
        "ORDER BY p.created_at DESC",
        current_vendor["id"],
    )
    return [
        {
            "id": r["id"],
            "amount": to_ksh(r["amount"]),
            "mpesa_transaction_id": r["mpesa_transaction_id"],
            "plan_id": r["plan_id"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    d1: D1 = Depends(get_d1),
    current_vendor: dict = Depends(get_current_vendor),
):
    payment = d1.query_one(
        "SELECT p.id, p.amount, p.mpesa_transaction_id, p.plan_id, p.created_at "
        "FROM payments p "
        "JOIN installment_plans ip ON ip.id = p.plan_id "
        "WHERE p.id = ? AND ip.vendor_id = ?",
        payment_id,
        current_vendor["id"],
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {
        "id": payment["id"],
        "amount": to_ksh(payment["amount"]),
        "mpesa_transaction_id": payment["mpesa_transaction_id"],
        "plan_id": payment["plan_id"],
        "created_at": payment["created_at"],
    }
