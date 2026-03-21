from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.customer import Customer
from app.models.vendor import Vendor
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.api.deps import get_current_vendor

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.post("/", response_model=CustomerResponse)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_vendor: Vendor = Depends(get_current_vendor)
):
    customer = Customer(
        full_name=customer_data.full_name,
        phone=customer_data.phone,
        national_id=customer_data.national_id,
        vendor_id=current_vendor.id
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

@router.get("/", response_model=list[CustomerResponse])
def get_customers(
    db: Session = Depends(get_db),
    current_vendor: Vendor = Depends(get_current_vendor)
):
    return db.query(Customer).filter(Customer.vendor_id == current_vendor.id).all()

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_vendor: Vendor = Depends(get_current_vendor)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.vendor_id == current_vendor.id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer