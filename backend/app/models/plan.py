import secrets
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class PlanStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    defaulted = "defaulted"

class InstallmentPlan(Base):
    __tablename__ = "installment_plans"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    deposit_paid = Column(Numeric(12, 2), nullable=False)
    amount_paid = Column(Numeric(12, 2), default=Decimal("0.00"))
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    tracking_token = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
        default=lambda: secrets.token_urlsafe(8),
    )
    status = Column(Enum(PlanStatus), default=PlanStatus.active)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="plans")
    payments = relationship("Payment", back_populates="plan")

    @property
    def balance(self):
        return self.total_price - self.deposit_paid - self.amount_paid
