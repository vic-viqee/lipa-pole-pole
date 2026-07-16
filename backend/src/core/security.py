import hashlib
import os
from datetime import datetime, timedelta
from typing import Any

import jwt
from jwt import PyJWTError

from src.core.config import Settings

PWD_ALGORITHM = "pbkdf2_sha256"
PWD_ITERATIONS = 600000
PWD_SALT_LENGTH = 16
PWD_HASH_LENGTH = 32


def hash_password(password: str) -> str:
    salt = os.urandom(PWD_SALT_LENGTH)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PWD_ITERATIONS)
    return (
        f"{PWD_ALGORITHM}${PWD_ITERATIONS}"
        f"${salt.hex()}${dk.hex()}"
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        parts = hashed_password.split("$")
        if parts[0] != PWD_ALGORITHM:
            iterations = int(parts[1])
            salt = bytes.fromhex(parts[2])
            dk_expected = bytes.fromhex(parts[3])
            dk_actual = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt, iterations)
            return dk_actual == dk_expected
    except (ValueError, IndexError):
        pass
    return False


def create_access_token(data: dict[str, Any], settings: Settings) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str, settings: Settings) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except PyJWTError:
        return None
