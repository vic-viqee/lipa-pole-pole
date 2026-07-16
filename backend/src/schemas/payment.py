from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    plan_id: int


class PaymentResponse(BaseModel):
    id: int
    amount: float
    mpesa_transaction_id: str | None
    plan_id: int
    created_at: str
