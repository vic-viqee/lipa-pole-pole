from pydantic import BaseModel


class CustomerCreate(BaseModel):
    full_name: str
    phone: str
    national_id: str


class CustomerResponse(BaseModel):
    id: int
    full_name: str
    phone: str
    national_id: str
    vendor_id: int
    created_at: str
