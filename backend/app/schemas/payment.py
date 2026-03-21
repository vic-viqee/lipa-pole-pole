from pydantic import BaseModel, Field
from datetime import datetime

class PaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    plan_id: int

class PaymentResponse(BaseModel):
    id: int
    amount: float
    mpesa_transaction_id: str | None
    plan_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
