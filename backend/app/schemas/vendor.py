from pydantic import BaseModel, EmailStr
from datetime import datetime

class VendorCreate(BaseModel):
    shop_name: str
    email: EmailStr
    phone: str
    password: str

class VendorLogin(BaseModel):
    email: EmailStr
    password: str

class VendorResponse(BaseModel):
    id: int
    shop_name: str
    email: str
    phone: str
    created_at: datetime

    model_config = {"from_attributes": True}