from fastapi import APIRouter, Depends, HTTPException

from src.core.deps import get_d1
from src.core.security import create_access_token, hash_password, verify_password
from src.core.config import get_settings
from src.db.d1 import D1
from src.schemas.vendor import VendorCreate, VendorLogin, VendorResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=VendorResponse)
def register(vendor_data: VendorCreate, d1: D1 = Depends(get_d1)):
    existing = d1.query_one(
        "SELECT id FROM vendors WHERE email = ?", vendor_data.email
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_phone = d1.query_one(
        "SELECT id FROM vendors WHERE phone = ?", vendor_data.phone
    )
    if existing_phone:
        raise HTTPException(status_code=400, detail="Phone already registered")

    hashed = hash_password(vendor_data.password)
    d1.execute(
        "INSERT INTO vendors (shop_name, email, phone, hashed_password) VALUES (?, ?, ?, ?)",
        vendor_data.shop_name,
        vendor_data.email,
        vendor_data.phone,
        hashed,
    )

    vendor = d1.query_one(
        "SELECT id, shop_name, email, phone, created_at FROM vendors WHERE email = ?",
        vendor_data.email,
    )
    if not vendor:
        raise HTTPException(status_code=500, detail="Failed to create vendor")
    return vendor


@router.post("/login")
def login(credentials: VendorLogin, d1: D1 = Depends(get_d1)):
    vendor = d1.query_one(
        "SELECT id, shop_name, email, phone, hashed_password FROM vendors WHERE email = ?",
        credentials.email,
    )
    if not vendor or not verify_password(credentials.password, vendor["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    settings = get_settings({})
    token = create_access_token({"sub": str(vendor["id"])}, settings)
    return {
        "access_token": token,
        "token_type": "bearer",
        "vendor": {"id": vendor["id"], "shop_name": vendor["shop_name"]},
    }
