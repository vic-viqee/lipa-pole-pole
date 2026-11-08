import base64
import json
import time
from datetime import datetime, timezone
from typing import Any

from js import AbortController, AbortError, AbortSignal, Object, fetch, setTimeout
from pyodide.ffi import to_js as _to_js

DEFAULT_MPESA_BASE_URL = "https://sandbox.safaricom.co.ke"
DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_TOKEN_REFRESH_SKEW_SECONDS = 60

_token_cache: dict[str, tuple[str, float]] = {}


def _js(obj: Any) -> Any:
    return _to_js(obj, dict_converter=Object.fromEntries)


class MpesaError(Exception):
    pass


class MpesaTimeoutError(MpesaError):
    pass


def _get_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def _generate_password(shortcode: str, passkey: str, timestamp: str) -> str:
    return base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()


def _format_phone(phone: str) -> str:
    cleaned = phone.strip().replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if cleaned.startswith("0"):
        cleaned = "254" + cleaned[1:]
    elif cleaned.startswith("7") and len(cleaned) == 9:
        cleaned = "254" + cleaned
    elif cleaned.startswith("1") and len(cleaned) == 9:
        cleaned = "254" + cleaned
    elif not cleaned.startswith("254"):
        cleaned = "254" + cleaned
    return cleaned


def _timeout_signal(timeout_seconds: int):
    # Prefer AbortSignal.timeout when available; fall back to AbortController+setTimeout.
    try:
        timeout_fn = getattr(AbortSignal, "timeout", None)
        if timeout_fn:
            return timeout_fn(int(timeout_seconds) * 1000)
    except Exception:
        pass
    try:
        controller = AbortController.new()
        setTimeout(lambda *_: controller.abort(), int(timeout_seconds) * 1000)
        return controller.signal
    except Exception:
        return None


async def _daraja_fetch(url: str, options: dict[str, Any], timeout_seconds: int, operation: str):
    opts = dict(options)
    signal = _timeout_signal(timeout_seconds)
    if signal is not None:
        opts["signal"] = signal
    try:
        return await fetch(url, _js(opts))
    except Exception as exc:
        name = getattr(exc, "name", "")
        if name == "AbortError" or isinstance(exc, AbortError) if "AbortError" in globals() else False:
            raise MpesaTimeoutError(f"{operation} timed out") from exc
        # Workers/Pyodide may surface aborts differently; keep message generic and non-sensitive.
        if "abort" in str(exc).lower() or "timeout" in str(exc).lower():
            raise MpesaTimeoutError(f"{operation} timed out") from exc
        raise MpesaError(f"{operation} failed") from exc


def _parse_token_expiry_seconds(data: dict[str, Any]) -> int:
    try:
        return max(int(data.get("expires_in", 3599)), 1)
    except (TypeError, ValueError):
        return 3599


async def get_access_token(
    consumer_key: str,
    consumer_secret: str,
    *,
    base_url: str = DEFAULT_MPESA_BASE_URL,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    refresh_skew_seconds: int = DEFAULT_TOKEN_REFRESH_SKEW_SECONDS,
) -> str:
    cache_key = f"{base_url.rstrip('/')}::{consumer_key}"
    now = time.time()
    cached = _token_cache.get(cache_key)
    if cached and cached[1] - refresh_skew_seconds > now:
        return cached[0]

    credentials = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
    url = f"{base_url.rstrip('/')}/oauth/v1/generate?grant_type=client_credentials"

    response = await _daraja_fetch(
        url,
        {
            "method": "GET",
            "headers": {"Authorization": f"Basic {credentials}"},
        },
        timeout_seconds,
        "M-Pesa token request",
    )

    if not response.ok:
        # Never include credentials/tokens/response body in surfaced errors.
        raise MpesaError(f"M-Pesa token request failed (HTTP {response.status})")

    text = await response.text()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MpesaError("M-Pesa token request failed") from exc

    token = data.get("access_token")
    if not token:
        raise MpesaError("M-Pesa token request failed")

    expires_in = _parse_token_expiry_seconds(data)
    _token_cache[cache_key] = (token, now + expires_in)
    return token


async def stk_push(
    access_token: str,
    shortcode: str,
    passkey: str,
    phone: str,
    amount_ksh: int,
    callback_url: str,
    account_reference: str,
    *,
    base_url: str = DEFAULT_MPESA_BASE_URL,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    timestamp = _get_timestamp()
    password = _generate_password(shortcode, passkey, timestamp)
    formatted_phone = _format_phone(phone)

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": str(amount_ksh),
        "PartyA": formatted_phone,
        "PartyB": shortcode,
        "PhoneNumber": formatted_phone,
        "CallBackURL": callback_url,
        "AccountReference": account_reference[:12],
        "TransactionDesc": "Lipa Pole Pole",
    }

    url = f"{base_url.rstrip('/')}/mpesa/stkpush/v1/processrequest"
    response = await _daraja_fetch(
        url,
        {
            "method": "POST",
            "headers": {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            "body": json.dumps(payload),
        },
        timeout_seconds,
        "M-Pesa STK request",
    )

    text = await response.text()

    if not response.ok:
        # Do not expose Daraja response body (may contain sensitive/error details).
        raise MpesaError(f"M-Pesa STK request failed (HTTP {response.status})")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MpesaError("M-Pesa STK request failed") from exc

    if data.get("ResponseCode") != "0":
        raise MpesaError(str(data.get("ResponseDescription") or "M-Pesa STK request failed"))

    return data


def parse_callback(body: dict[str, Any]) -> dict[str, Any]:
    stk = body.get("Body", {}).get("stkCallback", {})

    result: dict[str, Any] = {
        "merchant_request_id": stk.get("MerchantRequestID"),
        "checkout_request_id": stk.get("CheckoutRequestID"),
        "result_code": stk.get("ResultCode"),
        "result_desc": stk.get("ResultDesc"),
    }

    if result["result_code"] == 0:
        metadata = stk.get("CallbackMetadata", {}).get("Item", [])
        for item in metadata:
            name = item.get("Name")
            value = item.get("Value")
            if name == "Amount":
                result["amount"] = value
            elif name == "MpesaReceiptNumber":
                result["receipt_number"] = str(value)
            elif name == "PhoneNumber":
                result["phone"] = str(int(value))
            elif name == "TransactionDate":
                result["transaction_date"] = str(value)

    return result
