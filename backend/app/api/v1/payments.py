import logging
import re
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.payment import Payment
from app.models.plan import InstallmentPlan, PlanStatus
from app.models.mpesa_request import MpesaStkRequest
from app.models.vendor import Vendor
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.api.deps import get_current_vendor
from app.services.mpesa import stk_push

router = APIRouter(prefix="/payments", tags=["Payments"])
logger = logging.getLogger(__name__)


def to_money(value: float | int | str | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))

@router.post("/", response_model=PaymentResponse)
def record_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_vendor: Vendor = Depends(get_current_vendor)
):
    plan = db.query(InstallmentPlan).filter(
        InstallmentPlan.id == payment_data.plan_id,
        InstallmentPlan.vendor_id == current_vendor.id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status == PlanStatus.completed:
        raise HTTPException(status_code=400, detail="This plan is already completed")
    payment_amount = to_money(payment_data.amount)
    if payment_amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than 0")
    if payment_amount > plan.balance:
        raise HTTPException(status_code=400, detail=f"Amount exceeds remaining balance of {plan.balance}")

    payment = Payment(amount=payment_amount, plan_id=plan.id)
    db.add(payment)
    plan.amount_paid += payment_amount
    if plan.balance <= 0:
        plan.status = PlanStatus.completed
    db.commit()
    db.refresh(payment)
    return payment

@router.get("/plan/{plan_id}", response_model=list[PaymentResponse])
def get_payments_for_plan(
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
    return db.query(Payment).filter(Payment.plan_id == plan_id).all()

@router.post("/mpesa/stk/{tracking_token}")
def initiate_mpesa_payment(tracking_token: str, phone: str, amount: int, db: Session = Depends(get_db)):
    """Public endpoint — customer triggers M-Pesa STK push from tracking page"""
    plan = db.query(InstallmentPlan).filter(
        InstallmentPlan.tracking_token == tracking_token
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status == PlanStatus.completed:
        raise HTTPException(status_code=400, detail="This plan is already completed")
    if not re.fullmatch(r"254[17]\d{8}", phone):
        raise HTTPException(status_code=400, detail="Phone must start with 254 (e.g. 2547... or 2541...)")

    request_amount = to_money(amount)
    if request_amount <= 0 or request_amount > plan.balance:
        raise HTTPException(status_code=400, detail=f"Invalid amount. Balance is {plan.balance}")

    try:
        result = stk_push(phone=phone, amount=int(request_amount), plan_id=plan.id)
        checkout_request_id = result.get("CheckoutRequestID")
        merchant_request_id = result.get("MerchantRequestID")
        if not checkout_request_id:
            raise HTTPException(status_code=502, detail="Missing CheckoutRequestID from M-Pesa")

        stk_request = MpesaStkRequest(
            checkout_request_id=checkout_request_id,
            merchant_request_id=merchant_request_id,
            plan_id=plan.id,
            phone=phone,
            requested_amount=int(request_amount),
            status="pending",
        )
        db.add(stk_request)
        db.commit()

        return {
            "message": "STK push sent. Check your phone and enter your M-Pesa PIN.",
            "checkout_request_id": checkout_request_id,
            "merchant_request_id": merchant_request_id
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"M-Pesa error: {str(e)}")

@router.post("/mpesa/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    """Safaricom calls this after customer enters PIN"""
    body = await request.json()
    
    try:
        stk_callback = body.get("Body", {}).get("stkCallback", {})
        checkout_request_id = stk_callback.get("CheckoutRequestID")
        merchant_request_id = stk_callback.get("MerchantRequestID")
        result_code = stk_callback.get("ResultCode")

        if not checkout_request_id:
            logger.warning("M-Pesa callback missing CheckoutRequestID")
            return {"ResultCode": 0, "ResultDesc": "Accepted"}

        stk_request = db.query(MpesaStkRequest).filter(
            MpesaStkRequest.checkout_request_id == checkout_request_id
        ).first()
        if not stk_request:
            logger.warning("M-Pesa callback for unknown CheckoutRequestID: %s", checkout_request_id)
            return {"ResultCode": 0, "ResultDesc": "Accepted"}

        if not stk_request.merchant_request_id and merchant_request_id:
            stk_request.merchant_request_id = merchant_request_id

        if result_code != 0:
            stk_request.status = "failed"
            stk_request.processed_at = datetime.now(timezone.utc)
            db.commit()
            return {"ResultCode": 0, "ResultDesc": "Accepted"}

        metadata_items = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        metadata = {
            item.get("Name"): item.get("Value")
            for item in metadata_items
            if isinstance(item, dict) and "Name" in item
        }
        amount = to_money(metadata.get("Amount", stk_request.requested_amount))
        mpesa_code = metadata.get("MpesaReceiptNumber")

        if mpesa_code:
            existing = db.query(Payment).filter(Payment.mpesa_transaction_id == mpesa_code).first()
            if existing:
                stk_request.status = "completed"
                stk_request.processed_at = datetime.now(timezone.utc)
                db.commit()
                return {"ResultCode": 0, "ResultDesc": "Accepted"}

        plan = db.query(InstallmentPlan).filter(InstallmentPlan.id == stk_request.plan_id).first()
        if not plan:
            stk_request.status = "failed"
            stk_request.processed_at = datetime.now(timezone.utc)
            db.commit()
            logger.error("M-Pesa callback received for missing plan_id: %s", stk_request.plan_id)
            return {"ResultCode": 0, "ResultDesc": "Accepted"}

        if plan.status == PlanStatus.completed:
            stk_request.status = "completed"
            stk_request.processed_at = datetime.now(timezone.utc)
            db.commit()
            return {"ResultCode": 0, "ResultDesc": "Accepted"}

        if amount <= 0:
            stk_request.status = "failed"
            stk_request.processed_at = datetime.now(timezone.utc)
            db.commit()
            logger.error("M-Pesa callback amount invalid for checkout %s", checkout_request_id)
            return {"ResultCode": 0, "ResultDesc": "Accepted"}

        if amount > plan.balance:
            stk_request.status = "failed"
            stk_request.processed_at = datetime.now(timezone.utc)
            db.commit()
            logger.error("M-Pesa callback amount exceeds balance for checkout %s", checkout_request_id)
            return {"ResultCode": 0, "ResultDesc": "Accepted"}

        payment = Payment(
            amount=amount,
            mpesa_transaction_id=mpesa_code,
            plan_id=plan.id
        )
        db.add(payment)
        plan.amount_paid += amount
        if plan.balance <= 0:
            plan.status = PlanStatus.completed

        stk_request.status = "completed"
        stk_request.processed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        logger.exception("M-Pesa callback processing error: %s", e)

    return {"ResultCode": 0, "ResultDesc": "Accepted"}

@router.get("/public/{tracking_token}", response_model=list[PaymentResponse])
def get_payments_public(tracking_token: str, db: Session = Depends(get_db)):
    """Public endpoint for customer tracking page"""
    plan = db.query(InstallmentPlan).filter(
        InstallmentPlan.tracking_token == tracking_token
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return db.query(Payment).filter(Payment.plan_id == plan.id).all()
