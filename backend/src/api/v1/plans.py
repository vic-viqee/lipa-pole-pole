import secrets

from core.deps import extract_token, get_current_vendor, get_d1
from core.money import to_cents, to_ksh
from core.router import HTTPException, Router, json_response, parse_json_body
from core.validate import validate_non_negative_float, validate_positive_float, validate_positive_int, validate_required_string
from db.d1 import D1

router = Router(prefix="/api/v1/plans")


def row_to_plan_response(row: dict) -> dict:
    return {
        "id": row["id"],
        "product_name": row["product_name"],
        "total_price": to_ksh(row["total_price"]),
        "deposit_paid": to_ksh(row["deposit_paid"]),
        "amount_paid": to_ksh(row["amount_paid"]),
        "balance": to_ksh(row["total_price"] - row["deposit_paid"] - row["amount_paid"]),
        "tracking_token": row["tracking_token"],
        "status": row["status"],
        "customer_id": row["customer_id"],
        "vendor_id": row["vendor_id"],
        "created_at": row["created_at"],
    }


@router.post("")
async def create_plan(request, env, params):
    data = await parse_json_body(request)
    product_name = validate_required_string(data, "product_name")
    total_price = validate_positive_float(data, "total_price")
    deposit_paid = validate_non_negative_float(data, "deposit_paid")
    customer_id = validate_positive_int(data, "customer_id")

    token = extract_token(request)
    vendor = await get_current_vendor(env, token)
    d1: D1 = get_d1(env)

    customer = await d1.query_one(
        "SELECT id FROM customers WHERE id = ? AND vendor_id = ?",
        customer_id, vendor["id"],
    )
    if not customer:
        raise HTTPException(404, "Customer not found")

    total_price_cents = to_cents(total_price)
    deposit_paid_cents = to_cents(deposit_paid)

    if deposit_paid_cents > total_price_cents:
        raise HTTPException(400, "Deposit cannot exceed total price")

    tracking_token = secrets.token_urlsafe(8)

    await d1.execute(
        "INSERT INTO installment_plans "
        "(product_name, total_price, deposit_paid, amount_paid, customer_id, vendor_id, tracking_token) "
        "VALUES (?, ?, ?, 0, ?, ?, ?)",
        product_name, total_price_cents, deposit_paid_cents,
        customer_id, vendor["id"], tracking_token,
    )

    plan = await d1.query_one("SELECT * FROM installment_plans WHERE id = last_insert_rowid()")
    if not plan:
        raise HTTPException(500, "Failed to create plan")
    return json_response(row_to_plan_response(plan), status=201)


@router.get("")
async def list_plans(request, env, params):
    token = extract_token(request)
    vendor = await get_current_vendor(env, token)
    d1: D1 = get_d1(env)

    rows = await d1.query(
        "SELECT * FROM installment_plans WHERE vendor_id = ? ORDER BY created_at DESC",
        vendor["id"],
    )
    return json_response([row_to_plan_response(r) for r in rows])


@router.get("/{plan_id}")
async def get_plan(request, env, params):
    plan_id = int(params["plan_id"])
    token = extract_token(request)
    vendor = await get_current_vendor(env, token)
    d1: D1 = get_d1(env)

    plan = await d1.query_one(
        "SELECT * FROM installment_plans WHERE id = ? AND vendor_id = ?",
        plan_id, vendor["id"],
    )
    if not plan:
        raise HTTPException(404, "Plan not found")

    if plan["status"] == "active":
        remaining = plan["total_price"] - plan["deposit_paid"] - plan["amount_paid"]
        if remaining <= 0:
            await d1.execute(
                "UPDATE installment_plans SET status = 'completed' WHERE id = ?",
                plan_id,
            )
            plan["status"] = "completed"

    return json_response(row_to_plan_response(plan))


@router.get("/track/{tracking_token}")
async def track_plan_public(request, env, params):
    tracking_token = params["tracking_token"]
    d1: D1 = get_d1(env)

    plan = await d1.query_one(
        "SELECT p.*, v.shop_name AS vendor_name, c.full_name AS customer_name "
        "FROM installment_plans p "
        "JOIN vendors v ON v.id = p.vendor_id "
        "JOIN customers c ON c.id = p.customer_id "
        "WHERE p.tracking_token = ?",
        tracking_token,
    )
    if not plan:
        raise HTTPException(404, "Plan not found")

    base = row_to_plan_response(plan)
    base["vendor_name"] = plan["vendor_name"]
    base["customer_name"] = plan["customer_name"]
    return json_response(base)
