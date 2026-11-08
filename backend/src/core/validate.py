import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_KENYAN_PHONE_RE = re.compile(r"^254[17]\d{8}$")


def validate_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value))


def normalize_kenyan_phone(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("phone must be a string")
    phone = value.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+"):
        phone = phone[1:]
    if phone.startswith("0") and len(phone) == 10:
        phone = "254" + phone[1:]
    if phone.startswith("7") and len(phone) == 9:
        phone = "254" + phone
    if phone.startswith("1") and len(phone) == 9:
        phone = "254" + phone
    return phone


def validate_kenyan_phone(value: str) -> str:
    phone = normalize_kenyan_phone(value)
    if not _KENYAN_PHONE_RE.match(phone):
        raise ValueError("phone must be in format 254[17]XXXXXXXX")
    return phone


def validate_required_string(data: dict, key: str, max_len: int = 255) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    val = value.strip()
    if len(val) > max_len:
        raise ValueError(f"{key} too long (max {max_len})")
    return val


def validate_positive_float(data: dict, key: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number")
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return float(value)


def validate_non_negative_float(data: dict, key: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number")
    if value < 0:
        raise ValueError(f"{key} must be non-negative")
    return float(value)


def validate_positive_int(data: dict, key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value
