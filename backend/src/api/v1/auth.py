from core.config import get_settings
from core.deps import get_d1
from core.router import HTTPException, Router, json_response, parse_json_body
from core.security import create_access_token, hash_password, verify_password
from core.validate import validate_email, validate_kenyan_phone, validate_required_string
from db.d1 import D1

router = Router(prefix="/api/v1/auth")


@router.post("/register")
async def register(request, env, params):
    data = await parse_json_body(request)
    email = validate_required_string(data, "email")
    if not validate_email(email):
        raise HTTPException(400, "Invalid email")
    password = validate_required_string(data, "password")
    shop_name = validate_required_string(data, "shop_name")
    try:
        phone = validate_kenyan_phone(data.get("phone", ""))
    except ValueError as e:
        raise HTTPException(400, str(e))

    d1: D1 = get_d1(env)

    existing = await d1.query_one("SELECT id FROM vendors WHERE email = ?", email)
    if existing:
        raise HTTPException(400, "Email already registered")

    existing_phone = await d1.query_one("SELECT id FROM vendors WHERE phone = ?", phone)
    if existing_phone:
        raise HTTPException(400, "Phone already registered")

    hashed = hash_password(password)
    await d1.execute(
        "INSERT INTO vendors (shop_name, email, phone, hashed_password) VALUES (?, ?, ?, ?)",
        shop_name, email, phone, hashed,
    )

    vendor = await d1.query_one(
        "SELECT id, shop_name, email, phone, created_at FROM vendors WHERE email = ?",
        email,
    )
    if not vendor:
        raise HTTPException(500, "Failed to create vendor")
    return json_response(vendor, status=201)


@router.post("/login")
async def login(request, env, params):
    data = await parse_json_body(request)
    email = validate_required_string(data, "email")
    password = validate_required_string(data, "password")

    d1: D1 = get_d1(env)
    vendor = await d1.query_one(
        "SELECT id, shop_name, email, phone, hashed_password FROM vendors WHERE email = ?",
        email,
    )
    if not vendor or not verify_password(password, vendor["hashed_password"]):
        raise HTTPException(401, "Invalid email or password")

    # Re-hash if old iteration count is too high
    parts = vendor["hashed_password"].split("$")
    if parts[0] == "pbkdf2_sha256" and int(parts[1]) > 10000:
        new_hash = hash_password(password)
        await d1.execute("UPDATE vendors SET hashed_password = ? WHERE id = ?", new_hash, vendor["id"])

    token = create_access_token({"sub": str(vendor["id"])})
    return json_response({
        "access_token": token,
        "token_type": "bearer",
        "vendor": {"id": vendor["id"], "shop_name": vendor["shop_name"]},
    })
