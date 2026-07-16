from collections.abc import Generator
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from src.core.security import decode_access_token
from src.db.d1 import D1

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_d1(request: Request) -> D1:
    env: dict[str, Any] = request.scope["env"]
    return D1(env["DB"])


def get_current_vendor(
    token: str = Depends(oauth2_scheme),
    d1: D1 = Depends(get_d1),
) -> dict[str, Any]:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    vendor = d1.query_one(
        "SELECT id, shop_name, email, phone, created_at FROM vendors WHERE id = ?",
        int(payload["sub"]),
    )
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return vendor
