from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorLogin, VendorResponse
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=VendorResponse)
def register(vendor_data: VendorCreate, db: Session = Depends(get_db)):
    existing = db.query(Vendor).filter(Vendor.email == vendor_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    existing_phone = db.query(Vendor).filter(Vendor.phone == vendor_data.phone).first()
    if existing_phone:
        raise HTTPException(status_code=400, detail="Phone already registered")
    
    vendor = Vendor(
        shop_name=vendor_data.shop_name,
        email=vendor_data.email,
        phone=vendor_data.phone,
        hashed_password=hash_password(vendor_data.password)
    )
    db.add(vendor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email or phone already registered")
    db.refresh(vendor)
    return vendor

@router.post("/login")
def login(credentials: VendorLogin, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.email == credentials.email).first()
    if not vendor or not verify_password(credentials.password, vendor.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"sub": str(vendor.id)})
    return {"access_token": token, "token_type": "bearer", "vendor": {"id": vendor.id, "shop_name": vendor.shop_name}}
