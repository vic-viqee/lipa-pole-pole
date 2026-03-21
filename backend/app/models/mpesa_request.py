from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func
from app.db.base import Base


class MpesaStkRequest(Base):
    __tablename__ = "mpesa_stk_requests"

    id = Column(Integer, primary_key=True, index=True)
    checkout_request_id = Column(String, unique=True, index=True, nullable=False)
    merchant_request_id = Column(String, index=True, nullable=True)
    plan_id = Column(Integer, ForeignKey("installment_plans.id"), nullable=False)
    phone = Column(String, nullable=False)
    requested_amount = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
