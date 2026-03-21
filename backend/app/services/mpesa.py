import httpx
import base64
from datetime import datetime
from app.core.config import settings

SANDBOX_BASE_URL = "https://sandbox.safaricom.co.ke"

def get_access_token() -> str:
    credentials = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    
    response = httpx.get(
        f"{SANDBOX_BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
        headers={"Authorization": f"Basic {encoded}"}
    )
    response.raise_for_status()
    return response.json()["access_token"]

def get_password() -> tuple[str, str]:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(raw.encode()).decode()
    return password, timestamp

def stk_push(phone: str, amount: int, plan_id: int) -> dict:
    token = get_access_token()
    password, timestamp = get_password()

    # Normalize phone number to 254 format
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif phone.startswith("+"):
        phone = phone[1:]

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": f"Plan{plan_id}",
        "TransactionDesc": f"Lipa Polepole payment for plan {plan_id}"
    }

    response = httpx.post(
        f"{SANDBOX_BASE_URL}/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    response.raise_for_status()
    return response.json()