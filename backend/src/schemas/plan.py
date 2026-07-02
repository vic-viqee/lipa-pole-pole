from pydantic import BaseModel, Field, model_validator


class PlanCreate(BaseModel):
    product_name: str
    total_price: float = Field(gt=0)
    deposit_paid: float = Field(ge=0)
    customer_id: int

    @model_validator(mode="after")
    def validate_amounts(self):
        if self.deposit_paid > self.total_price:
            raise ValueError("deposit_paid cannot exceed total_price")
        return self


class PlanResponse(BaseModel):
    id: int
    product_name: str
    total_price: float
    deposit_paid: float
    amount_paid: float
    balance: float
    tracking_token: str
    status: str
    customer_id: int
    vendor_id: int
    created_at: str


class PublicPlanResponse(PlanResponse):
    vendor_name: str
    customer_name: str
