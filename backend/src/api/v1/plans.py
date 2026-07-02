import secrets

from fastapi import APIRouter, Depends, HTTPException

from src.core.deps import get_current_vendor, get_d1
from src.core.money import to_cents, to_ksh
from src.db.d1 import D1
from src.schemas.plan import PlanCreate, PlanResponse, PublicPlanResponse

router = APIRouter(prefix="/plans", tags=["Plans"])


def row_to_plan_response(row: dict) -> dict:
    return {
        "id": row["id"],
        "product_name": row["product_name"],
        "total_price": to_ksh(row["total_price"]),
        "deposit_paid": to_ksh(row["deposit_paid"]),
        "amount_paid": to_ksh(row["amount_paid"]),
        "balance": to_ksh(row["total_price"] - row["deposit_paid"] - row["amount_paid"]),
        "tracking_token": row["tracking_token"],
        "status": row["status"],
        "customer_id": row["customer_id"],
        "vendor_id": row["vendor_id"],
        "created_at": row["created_at"],
    }


@router.post("/", response_model=PlanResponse)
def create_plan(
    plan_data: PlanCreate,
    d1: D1 = Depends(get_d1),
    current_vendor: dict = Depends(get_current_vendor),
):
    customer = d1.query_one(
        "SELECT id FROM customers WHERE id = ? AND vendor_id = ?",
        plan_data.customer_id,
        current_vendor["id"],
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    total_price_cents = to_cents(plan_data.total_price)
    deposit_paid_cents = to_cents(plan_data.deposit_paid)

    if deposit_paid_cents > total_price_cents:
        raise HTTPException(status_code=400, detail="Deposit cannot exceed total price")

    tracking_token = secrets.token_urlsafe(8)

    d1.execute(
        "INSERT INTO installment_plans "
        "(product_name, total_price, deposit_paid, amount_paid, customer_id, vendor_id, tracking_token) "
        "VALUES (?, ?, ?, 0, ?, ?, ?)",
        plan_data.product_name,
        total_price_cents,
        deposit_paid_cents,
        plan_data.customer_id,
        current_vendor["id"],
        tracking_token,
    )

    plan = d1.query_one(
        "SELECT * FROM installment_plans WHERE id = last_insert_rowid()"
    )
    if not plan:
        raise HTTPException(status_code=500, detail="Failed to create plan")
    return row_to_plan_response(plan)


@router.get("/", response_model=list[PlanResponse])
def get_plans(
    d1: D1 = Depends(get_d1),
    current_vendor: dict = Depends(get_current_vendor),
):
    rows = d1.query(
        "SELECT * FROM installment_plans WHERE vendor_id = ? ORDER BY created_at DESC",
        current_vendor["id"],
    )
    return [row_to_plan_response(r) for r in rows]


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: int,
    d1: D1 = Depends(get_d1),
    current_vendor: dict = Depends(get_current_vendor),
):
    plan = d1.query_one(
        "SELECT * FROM installment_plans WHERE id = ? AND vendor_id = ?",
        plan_id,
        current_vendor["id"],
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return row_to_plan_response(plan)


@router.get("/track/{tracking_token}", response_model=PublicPlanResponse)
def track_plan_public(tracking_token: str, d1: D1 = Depends(get_d1)):
    plan = d1.query_one(
        "SELECT p.*, v.shop_name AS vendor_name, c.full_name AS customer_name "
        "FROM installment_plans p "
        "JOIN vendors v ON v.id = p.vendor_id "
        "JOIN customers c ON c.id = p.customer_id "
        "WHERE p.tracking_token = ?",
        tracking_token,
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    base = row_to_plan_response(plan)
    base["vendor_name"] = plan["vendor_name"]
    base["customer_name"] = plan["customer_name"]
    return base
