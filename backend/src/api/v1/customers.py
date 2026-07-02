from fastapi import APIRouter, Depends, HTTPException

from src.core.deps import get_current_vendor, get_d1
from src.db.d1 import D1
from src.schemas.customer import CustomerCreate, CustomerResponse

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("/", response_model=CustomerResponse)
def create_customer(
    customer_data: CustomerCreate,
    d1: D1 = Depends(get_d1),
    current_vendor: dict = Depends(get_current_vendor),
):
    d1.execute(
        "INSERT INTO customers (full_name, phone, national_id, vendor_id) VALUES (?, ?, ?, ?)",
        customer_data.full_name,
        customer_data.phone,
        customer_data.national_id,
        current_vendor["id"],
    )

    customer = d1.query_one(
        "SELECT id, full_name, phone, national_id, vendor_id, created_at "
        "FROM customers WHERE id = last_insert_rowid()"
    )
    if not customer:
        raise HTTPException(status_code=500, detail="Failed to create customer")
    return customer


@router.get("/", response_model=list[CustomerResponse])
def get_customers(
    d1: D1 = Depends(get_d1),
    current_vendor: dict = Depends(get_current_vendor),
):
    return d1.query(
        "SELECT id, full_name, phone, national_id, vendor_id, created_at "
        "FROM customers WHERE vendor_id = ? ORDER BY created_at DESC",
        current_vendor["id"],
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    d1: D1 = Depends(get_d1),
    current_vendor: dict = Depends(get_current_vendor),
):
    customer = d1.query_one(
        "SELECT id, full_name, phone, national_id, vendor_id, created_at "
        "FROM customers WHERE id = ? AND vendor_id = ?",
        customer_id,
        current_vendor["id"],
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
