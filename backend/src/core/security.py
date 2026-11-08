import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from core.config import get_settings

PWD_ALGORITHM = "pbkdf2_sha256"
PWD_ITERATIONS = 1000
PWD_SALT_LENGTH = 16


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _hmac_sha256(key: str, message: str) -> bytes:
    return hmac.new(key.encode(), message.encode(), hashlib.sha256).digest()


def hash_password(password: str) -> str:
    salt = os.urandom(PWD_SALT_LENGTH)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PWD_ITERATIONS)
    return f"{PWD_ALGORITHM}${PWD_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        parts = hashed_password.split("$")
        if parts[0] == PWD_ALGORITHM:
            iterations = int(parts[1])
            salt = bytes.fromhex(parts[2])
            dk_expected = bytes.fromhex(parts[3])
            dk_actual = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt, iterations)
            return dk_actual == dk_expected
    except (ValueError, IndexError):
        pass
    return False


def create_access_token(data: dict[str, Any]) -> str:
    settings = get_settings()
    to_encode = data.copy()
    to_encode["exp"] = int(time.time()) + settings["ACCESS_TOKEN_EXPIRE_MINUTES"] * 60
    header_b64 = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload_b64 = _b64url_encode(json.dumps(to_encode, separators=(",", ":")).encode())
    sig = _b64url_encode(_hmac_sha256(settings["SECRET_KEY"], f"{header_b64}.{payload_b64}"))
    return f"{header_b64}.{payload_b64}.{sig}"


def decode_access_token(token: str) -> dict[str, Any] | None:
    settings = get_settings()
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        expected_sig = _b64url_encode(_hmac_sha256(settings["SECRET_KEY"], f"{header_b64}.{payload_b64}"))
        if sig_b64 != expected_sig:
            return None
        payload = json.loads(_b64url_decode(payload_b64))
        if payload.get("exp") and int(payload["exp"]) < time.time():
            return None
        return payload
    except (ValueError, IndexError, json.JSONDecodeError):
        return None
