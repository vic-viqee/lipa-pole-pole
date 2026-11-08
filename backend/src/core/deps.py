from typing import Any

from core.router import HTTPException
from core.security import decode_access_token
from db.d1 import D1


def get_d1(env: dict[str, Any]) -> D1:
    return D1(env["DB"])


async def get_current_vendor(env: dict[str, Any], token: str | None) -> dict[str, Any]:
    if not token:
        raise HTTPException(401, "Authorization header required")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")

    d1 = get_d1(env)
    vendor = await d1.query_one(
        "SELECT id, shop_name, email, phone, created_at FROM vendors WHERE id = ?",
        int(payload["sub"]),
    )
    if not vendor:
        raise HTTPException(404, "Vendor not found")

    return vendor


def extract_token(request: Any) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None
