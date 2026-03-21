from sqlalchemy import Column, Integer, Numeric, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    mpesa_transaction_id = Column(String, nullable=True)
    plan_id = Column(Integer, ForeignKey("installment_plans.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    plan = relationship("InstallmentPlan", back_populates="payments")
