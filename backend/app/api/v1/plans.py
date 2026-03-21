from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.plan import InstallmentPlan, PlanStatus
from app.models.customer import Customer
from app.models.vendor import Vendor
from app.schemas.plan import PlanCreate, PlanResponse
from app.api.deps import get_current_vendor

router = APIRouter(prefix="/plans", tags=["Plans"])


def to_money(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))

@router.post("/", response_model=PlanResponse)
def create_plan(
    plan_data: PlanCreate,
    db: Session = Depends(get_db),
    current_vendor: Vendor = Depends(get_current_vendor)
):
    customer = db.query(Customer).filter(
        Customer.id == plan_data.customer_id,
        Customer.vendor_id == current_vendor.id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    total_price = to_money(plan_data.total_price)
    deposit_paid = to_money(plan_data.deposit_paid)
    if total_price <= 0:
        raise HTTPException(status_code=400, detail="Total price must be greater than 0")
    if deposit_paid < 0:
        raise HTTPException(status_code=400, detail="Deposit cannot be negative")

    if deposit_paid > total_price:
        raise HTTPException(status_code=400, detail="Deposit cannot exceed total price")

    plan = InstallmentPlan(
        product_name=plan_data.product_name,
        total_price=total_price,
        deposit_paid=deposit_paid,
        amount_paid=Decimal("0.00"),
        customer_id=plan_data.customer_id,
        vendor_id=current_vendor.id
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

@router.get("/", response_model=list[PlanResponse])
def get_plans(
    db: Session = Depends(get_db),
    current_vendor: Vendor = Depends(get_current_vendor)
):
    return db.query(InstallmentPlan).filter(InstallmentPlan.vendor_id == current_vendor.id).all()

@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_vendor: Vendor = Depends(get_current_vendor)
):
    plan = db.query(InstallmentPlan).filter(
        InstallmentPlan.id == plan_id,
        InstallmentPlan.vendor_id == current_vendor.id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

@router.get("/track/{tracking_token}", response_model=PlanResponse)
def track_plan_public(tracking_token: str, db: Session = Depends(get_db)):
    """Public endpoint — customers use this to check their balance"""
    plan = db.query(InstallmentPlan).filter(
        InstallmentPlan.tracking_token == tracking_token
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan
