from core.deps import extract_token, get_current_vendor, get_d1
from core.router import HTTPException, Router, json_response, parse_json_body
from core.validate import validate_kenyan_phone, validate_required_string
from db.d1 import D1

router = Router(prefix="/api/v1/customers")


@router.post("")
async def create_customer(request, env, params):
    data = await parse_json_body(request)
    full_name = validate_required_string(data, "full_name")
    try:
        phone = validate_kenyan_phone(data.get("phone", ""))
    except ValueError as e:
        raise HTTPException(400, str(e))
    national_id = validate_required_string(data, "national_id")

    token = extract_token(request)
    vendor = await get_current_vendor(env, token)
    d1: D1 = get_d1(env)

    await d1.execute(
        "INSERT INTO customers (full_name, phone, national_id, vendor_id) VALUES (?, ?, ?, ?)",
        full_name, phone, national_id, vendor["id"],
    )

    customer = await d1.query_one(
        "SELECT id, full_name, phone, national_id, vendor_id, created_at "
        "FROM customers WHERE id = last_insert_rowid()"
    )
    if not customer:
        raise HTTPException(500, "Failed to create customer")
    return json_response(customer, status=201)


@router.get("")
async def list_customers(request, env, params):
    token = extract_token(request)
    vendor = await get_current_vendor(env, token)
    d1: D1 = get_d1(env)

    rows = await d1.query(
        "SELECT id, full_name, phone, national_id, vendor_id, created_at "
        "FROM customers WHERE vendor_id = ? ORDER BY created_at DESC",
        vendor["id"],
    )
    return json_response(rows)


@router.get("/{customer_id}")
async def get_customer(request, env, params):
    customer_id = int(params["customer_id"])
    token = extract_token(request)
    vendor = await get_current_vendor(env, token)
    d1: D1 = get_d1(env)

    customer = await d1.query_one(
        "SELECT id, full_name, phone, national_id, vendor_id, created_at "
        "FROM customers WHERE id = ? AND vendor_id = ?",
        customer_id, vendor["id"],
    )
    if not customer:
        raise HTTPException(404, "Customer not found")
    return json_response(customer)
