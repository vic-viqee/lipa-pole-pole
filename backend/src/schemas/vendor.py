from datetime import datetime

from pydantic import BaseModel, EmailStr


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
    created_at: str
