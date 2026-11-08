from datetime import datetime, timezone

from core.config import get_settings
from core.deps import extract_token, get_current_vendor, get_d1
from core.money import to_cents, to_ksh
from core.router import HTTPException, Router, json_response, parse_json_body
from core.validate import validate_kenyan_phone, validate_positive_float, validate_positive_int
from db.d1 import D1
from services.mpesa import (
    MpesaError,
    MpesaTimeoutError,
    get_access_token,
    parse_callback,
    stk_push as mpesa_stk_push,
)

router = Router(prefix="/api/v1/payments")


def _mask_id(value: str | None) -> str:
    if not value:
        return "-"
    text = str(value)
    if len(text) <= 8:
        return "***"
    return f"{text[:4]}...{text[-4:]}"


def _log_mpesa_callback(event: str, **fields) -> None:
    # Redacted: never log full callback bodies, phone numbers, tokens, keys, or secrets.
    safe = {k: v for k, v in fields.items() if v is not None}
    parts = " ".join(f"{k}={v}" for k, v in safe.items())
    print(f"[mpesa_callback] event={event} {parts}".rstrip())


def _callback_ack() -> dict:
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.post("")
async def init_payment(request, env, params):
    data = await parse_json_body(request)
    amount = validate_positive_float(data, "amount")
    plan_id = validate_positive_int(data, "plan_id")

    token = extract_token(request)
    vendor = await get_current_vendor(env, token)
    d1: D1 = get_d1(env)

    plan = await d1.query_one(
        "SELECT id, total_price, deposit_paid, amount_paid, status, vendor_id "
        "FROM installment_plans WHERE id = ? AND vendor_id = ?",
        plan_id, vendor["id"],
    )
    if not plan:
        raise HTTPException(404, "Plan not found")
    if plan["status"] != "active":
        raise HTTPException(400, "Plan is not active")

    amount_cents = to_cents(amount)
    remaining = plan["total_price"] - plan["deposit_paid"] - plan["amount_paid"]
    if amount_cents > remaining:
        raise HTTPException(
            400,
            f"Amount exceeds remaining balance of {to_ksh(remaining)}",
        )

    recorded_at = datetime.now(timezone.utc).isoformat()

    # Manual/vendor-recorded payments are saved as 'confirmed' and credited immediately.
    # This matches the current frontend flow (vendor records a cash/offline receipt and the
    # UI refreshes plan balance/history). Guarded batch ensures payment insert + balance
    # update + completion succeed or fail together, and prevents over-credit at commit time.
    batch_results = await d1.batch([
        (
            "INSERT INTO payments (amount, plan_id, status, recorded_by_vendor_id, created_at) "
            "SELECT ?, ?, 'confirmed', ?, ? "
            "WHERE EXISTS ("
            "  SELECT 1 FROM installment_plans p "
            "  WHERE p.id = ? AND p.vendor_id = ? AND p.status = 'active' "
            "    AND (p.total_price - p.deposit_paid - p.amount_paid) >= ?"
            ")",
            [
                amount_cents, plan_id, vendor["id"], recorded_at,
                plan_id, vendor["id"], amount_cents,
            ],
        ),
        (
            "UPDATE installment_plans SET amount_paid = amount_paid + ? "
            "WHERE id = ? AND vendor_id = ? AND status = 'active' "
            "AND (total_price - deposit_paid - amount_paid) >= ? "
            "AND EXISTS ("
            "  SELECT 1 FROM payments "
            "  WHERE plan_id = ? AND recorded_by_vendor_id = ? AND created_at = ? "
            "    AND amount = ? AND status = 'confirmed'"
            ")",
            [
                amount_cents, plan_id, vendor["id"], amount_cents,
                plan_id, vendor["id"], recorded_at, amount_cents,
            ],
        ),
        (
            "UPDATE installment_plans SET status = 'completed' "
            "WHERE id = ? AND vendor_id = ? AND status = 'active' "
            "AND (total_price - deposit_paid - amount_paid) <= 0 "
            "AND EXISTS ("
            "  SELECT 1 FROM payments "
            "  WHERE plan_id = ? AND recorded_by_vendor_id = ? AND created_at = ? "
            "    AND amount = ? AND status = 'confirmed'"
            ")",
            [plan_id, vendor["id"], plan_id, vendor["id"], recorded_at, amount_cents],
        ),
    ])

    def _changes(res):
        if not isinstance(res, dict):
            return None
        meta = res.get("meta") or {}
        if isinstance(meta, dict):
            for key in ("changes", "rows_written", "changed_db_rows"):
                if key in meta and meta[key] is not None:
                    try:
                        return int(meta[key])
                    except (TypeError, ValueError):
                        return None
        return None

    insert_changes = _changes(batch_results[0]) if isinstance(batch_results, list) and batch_results else None
    if insert_changes == 0:
        raise HTTPException(409, "Payment could not be recorded; plan may have changed")

    updated_plan = await d1.query_one(
        "SELECT total_price, deposit_paid, amount_paid FROM installment_plans WHERE id = ?",
        plan_id,
    )
    if not updated_plan:
        raise HTTPException(500, "Failed to load updated plan")

    remaining = updated_plan["total_price"] - updated_plan["deposit_paid"] - updated_plan["amount_paid"]
    payment = await d1.query_one(
        "SELECT id, amount, mpesa_transaction_id, plan_id, created_at "
        "FROM payments "
        "WHERE plan_id = ? AND recorded_by_vendor_id = ? AND created_at = ? AND amount = ? "
        "  AND status = 'confirmed' "
        "ORDER BY id DESC LIMIT 1",
        plan_id, vendor["id"], recorded_at, amount_cents,
    )
    if not payment:
        raise HTTPException(500, "Failed to create payment")

    return json_response({
        "id": payment["id"],
        "amount": to_ksh(payment["amount"]),
        "mpesa_transaction_id": payment["mpesa_transaction_id"],
        "plan_id": payment["plan_id"],
        "created_at": payment["created_at"],
        "remaining_balance": to_ksh(max(remaining, 0)),
    }, status=201)


@router.get("")
async def list_payments(request, env, params):
    token = extract_token(request)
    vendor = await get_current_vendor(env, token)
    d1: D1 = get_d1(env)

    rows = await d1.query(
        "SELECT p.id, p.amount, p.mpesa_transaction_id, p.plan_id, p.created_at "
        "FROM payments p "
        "JOIN installment_plans ip ON ip.id = p.plan_id "
        "WHERE ip.vendor_id = ? "
        "ORDER BY p.created_at DESC",
        vendor["id"],
    )
    return json_response([
        {
            "id": r["id"],
            "amount": to_ksh(r["amount"]),
            "mpesa_transaction_id": r["mpesa_transaction_id"],
            "plan_id": r["plan_id"],
            "created_at": r["created_at"],
        }
        for r in rows
    ])


@router.get("/public/{tracking_token}")
async def list_payments_public(request, env, params):
    tracking_token = params["tracking_token"]
    d1: D1 = get_d1(env)

    plan = await d1.query_one(
        "SELECT id FROM installment_plans WHERE tracking_token = ?",
        tracking_token,
    )
    if not plan:
        raise HTTPException(404, "Plan not found")

    rows = await d1.query(
        "SELECT id, amount, mpesa_transaction_id, plan_id, created_at "
        "FROM payments WHERE plan_id = ? ORDER BY created_at DESC",
        plan["id"],
    )
    return json_response([
        {
            "id": r["id"],
            "amount": to_ksh(r["amount"]),
            "mpesa_transaction_id": r["mpesa_transaction_id"],
            "plan_id": r["plan_id"],
            "created_at": r["created_at"],
        }
        for r in rows
    ])


@router.get("/plan/{plan_id}")
async def list_payments_for_plan(request, env, params):
    plan_id = int(params["plan_id"])
    token = extract_token(request)
    vendor = await get_current_vendor(env, token)
    d1: D1 = get_d1(env)

    plan = await d1.query_one(
        "SELECT id FROM installment_plans WHERE id = ? AND vendor_id = ?",
        plan_id, vendor["id"],
    )
    if not plan:
        raise HTTPException(404, "Plan not found")

    rows = await d1.query(
        "SELECT id, amount, mpesa_transaction_id, plan_id, created_at "
        "FROM payments WHERE plan_id = ? ORDER BY created_at DESC",
        plan_id,
    )
    return json_response([
        {
            "id": r["id"],
            "amount": to_ksh(r["amount"]),
            "mpesa_transaction_id": r["mpesa_transaction_id"],
            "plan_id": r["plan_id"],
            "created_at": r["created_at"],
        }
        for r in rows
    ])


@router.get("/{payment_id}")
async def get_payment(request, env, params):
    payment_id = int(params["payment_id"])
    token = extract_token(request)
    vendor = await get_current_vendor(env, token)
    d1: D1 = get_d1(env)

    payment = await d1.query_one(
        "SELECT p.id, p.amount, p.mpesa_transaction_id, p.plan_id, p.created_at "
        "FROM payments p "
        "JOIN installment_plans ip ON ip.id = p.plan_id "
        "WHERE p.id = ? AND ip.vendor_id = ?",
        payment_id, vendor["id"],
    )
    if not payment:
        raise HTTPException(404, "Payment not found")
    return json_response({
        "id": payment["id"],
        "amount": to_ksh(payment["amount"]),
        "mpesa_transaction_id": payment["mpesa_transaction_id"],
        "plan_id": payment["plan_id"],
        "created_at": payment["created_at"],
    })


@router.post("/mpesa/stk/{tracking_token}")
async def stk_push(request, env, params):
    tracking_token = params["tracking_token"]
    data = await parse_json_body(request)
    try:
        phone = validate_kenyan_phone(data.get("phone", ""))
    except ValueError as e:
        raise HTTPException(400, str(e))
    amount_ksh = data.get("amount")

    if not isinstance(amount_ksh, (int, float)) or amount_ksh <= 0:
        raise HTTPException(400, "Positive amount required")

    d1 = get_d1(env)
    plan = await d1.query_one(
        "SELECT id, total_price, deposit_paid, amount_paid, status "
        "FROM installment_plans WHERE tracking_token = ?",
        tracking_token,
    )
    if not plan:
        raise HTTPException(404, "Plan not found")
    if plan["status"] != "active":
        raise HTTPException(400, "Plan is not active")

    amount_cents = to_cents(amount_ksh)
    remaining = plan["total_price"] - plan["deposit_paid"] - plan["amount_paid"]
    if amount_cents > remaining:
        raise HTTPException(
            400,
            f"Amount exceeds remaining balance of {to_ksh(remaining)}",
        )

    settings = get_settings()
    consumer_key = settings.get("MPESA_CONSUMER_KEY", "")
    consumer_secret = settings.get("MPESA_CONSUMER_SECRET", "")
    shortcode = settings.get("MPESA_SHORTCODE", "")
    passkey = settings.get("MPESA_PASSKEY", "")
    callback_url = settings.get("MPESA_CALLBACK_URL", "")
    base_url = settings.get("MPESA_BASE_URL", "https://sandbox.safaricom.co.ke")
    timeout_seconds = int(settings.get("MPESA_TIMEOUT_SECONDS", 15))
    token_refresh_skew = int(settings.get("MPESA_TOKEN_REFRESH_SKEW_SECONDS", 60))

    if not all([consumer_key, consumer_secret, shortcode, passkey, callback_url]):
        raise HTTPException(500, "M-Pesa not configured")

    try:
        token = await get_access_token(
            consumer_key,
            consumer_secret,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            refresh_skew_seconds=token_refresh_skew,
        )
        result = await mpesa_stk_push(
            token, shortcode, passkey, phone, int(amount_ksh),
            callback_url, tracking_token,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
        )
    except MpesaTimeoutError:
        raise HTTPException(502, "M-Pesa request timed out. Please try again.")
    except MpesaError:
        raise HTTPException(502, "M-Pesa request failed. Please try again.")

    checkout_request_id = result.get("CheckoutRequestID", "")
    merchant_request_id = result.get("MerchantRequestID", "")

    await d1.execute(
        "INSERT INTO mpesa_stk_requests "
        "(checkout_request_id, merchant_request_id, plan_id, phone, requested_amount, status) "
        "VALUES (?, ?, ?, ?, ?, 'pending')",
        checkout_request_id, merchant_request_id, plan["id"], phone.strip(), amount_cents,
    )

    return json_response({
        "checkout_request_id": checkout_request_id,
        "merchant_request_id": merchant_request_id,
        "response_description": result.get("ResponseDescription", ""),
        "amount_ksh": int(amount_ksh),
    })


# M-Pesa callback safety checks (defense-in-depth):
# - CheckoutRequestID binding: only a known, pending STK request can mutate money state,
#   preventing forged callbacks from crediting arbitrary plans.
# - Amount equality: callback amount must match requested_amount stored at STK initiation,
#   preventing tampering or mismatched payloads from crediting the wrong value.
# - Remaining-balance-at-commit: the plan's remaining balance is rechecked at commit time
#   (not only at STK initiation) to prevent over-credit from races or concurrent credits.
# - Receipt uniqueness: mpesa_receipt_number is unique (DB index) so duplicate/replayed
#   deliveries cannot insert duplicate completed payments.
# - Atomic batch: payment insert, plan balance/status updates, and STK status update run in
#   one D1 batch with guarded WHERE clauses so they succeed/fail together and cannot
#   partially credit on guard failure.
# - Replay no-op: already-processed CheckoutRequestIDs or duplicate receipts return success
#   with no side effects so Safaricom retries are safe.
# - Non-leaking responses: callers receive only generic ACKs; internal details are logged
#   server-side without full payloads, phones, tokens, or raw exception text.
@router.post("/mpesa/callback")
async def mpesa_callback(request, env, params):
    try:
        body = await parse_json_body(request)
        cb = parse_callback(body)

        checkout_request_id = cb.get("checkout_request_id")
        if not checkout_request_id:
            _log_mpesa_callback("reject", reason="missing_checkout_request_id")
            return json_response(_callback_ack())

        d1 = get_d1(env)
        stk = await d1.query_one(
            "SELECT id, plan_id, status, requested_amount "
            "FROM mpesa_stk_requests WHERE checkout_request_id = ?",
            checkout_request_id,
        )
        if not stk:
            _log_mpesa_callback(
                "reject", reason="unknown_checkout_request_id", checkout=_mask_id(checkout_request_id)
            )
            return json_response(_callback_ack())

        now = datetime.now(timezone.utc).isoformat()
        checkout_masked = _mask_id(checkout_request_id)

        if stk["status"] != "pending":
            _log_mpesa_callback(
                "noop", reason="stk_not_pending", checkout=checkout_masked, status=stk["status"]
            )
            return json_response(_callback_ack())

        result_code = cb.get("result_code")
        if result_code != 0:
            await d1.batch([
                (
                    "UPDATE mpesa_stk_requests SET status = 'failed', processed_at = ? "
                    "WHERE id = ? AND status = 'pending'",
                    [now, stk["id"]],
                )
            ])
            _log_mpesa_callback(
                "failed", checkout=checkout_masked, result_code=str(result_code)
            )
            return json_response(_callback_ack())

        receipt = cb.get("receipt_number")
        if not receipt:
            _log_mpesa_callback("reject", reason="missing_receipt", checkout=checkout_masked)
            return json_response(_callback_ack())

        existing_receipt = await d1.query_one(
            "SELECT id FROM payments WHERE mpesa_receipt_number = ?",
            str(receipt),
        )
        if existing_receipt:
            await d1.batch([
                (
                    "UPDATE mpesa_stk_requests SET status = 'completed', processed_at = ? "
                    "WHERE id = ? AND status = 'pending'",
                    [now, stk["id"]],
                )
            ])
            _log_mpesa_callback("noop", reason="duplicate_receipt", checkout=checkout_masked)
            return json_response(_callback_ack())

        amount_raw = cb.get("amount")
        if amount_raw is None:
            _log_mpesa_callback("reject", reason="missing_amount", checkout=checkout_masked)
            return json_response(_callback_ack())

        try:
            amount_cents = to_cents(float(amount_raw))
        except (TypeError, ValueError):
            _log_mpesa_callback("reject", reason="invalid_amount", checkout=checkout_masked)
            return json_response(_callback_ack())

        if amount_cents <= 0:
            _log_mpesa_callback("reject", reason="non_positive_amount", checkout=checkout_masked)
            return json_response(_callback_ack())

        if int(amount_cents) != int(stk["requested_amount"]):
            _log_mpesa_callback(
                "reject",
                reason="amount_mismatch",
                checkout=checkout_masked,
                expected_cents=str(stk["requested_amount"]),
                got_cents=str(amount_cents),
            )
            return json_response(_callback_ack())

        plan = await d1.query_one(
            "SELECT id, total_price, deposit_paid, amount_paid, status "
            "FROM installment_plans WHERE id = ?",
            stk["plan_id"],
        )
        if not plan:
            _log_mpesa_callback("reject", reason="plan_not_found", checkout=checkout_masked)
            return json_response(_callback_ack())

        remaining = int(plan["total_price"]) - int(plan["deposit_paid"]) - int(plan["amount_paid"])
        if amount_cents > remaining or plan["status"] != "active":
            _log_mpesa_callback(
                "reject",
                reason="exceeds_remaining_or_inactive",
                checkout=checkout_masked,
                remaining_cents=str(max(remaining, 0)),
                plan_status=str(plan["status"]),
            )
            return json_response(_callback_ack())

        phone = str(cb.get("phone") or "")
        receipt_str = str(receipt)

        try:
            batch_results = await d1.batch([
                (
                    "INSERT INTO payments "
                    "(amount, mpesa_transaction_id, plan_id, status, phone, mpesa_receipt_number) "
                    "SELECT ?, ?, ?, 'completed', ?, ? "
                    "WHERE EXISTS ("
                    "  SELECT 1 FROM mpesa_stk_requests s "
                    "  JOIN installment_plans p ON p.id = s.plan_id "
                    "  WHERE s.id = ? AND s.status = 'pending' "
                    "    AND p.id = ? AND p.status = 'active' "
                    "    AND (p.total_price - p.deposit_paid - p.amount_paid) >= ?"
                    ")",
                    [
                        amount_cents, checkout_request_id, stk["plan_id"], phone, receipt_str,
                        stk["id"], stk["plan_id"], amount_cents,
                    ],
                ),
                (
                    "UPDATE installment_plans SET amount_paid = amount_paid + ? "
                    "WHERE id = ? AND status = 'active' "
                    "AND (total_price - deposit_paid - amount_paid) >= ? "
                    "AND EXISTS (SELECT 1 FROM mpesa_stk_requests WHERE id = ? AND status = 'pending') "
                    "AND EXISTS (SELECT 1 FROM payments WHERE mpesa_receipt_number = ? AND plan_id = ?)",
                    [amount_cents, stk["plan_id"], amount_cents, stk["id"], receipt_str, stk["plan_id"]],
                ),
                (
                    "UPDATE installment_plans SET status = 'completed' "
                    "WHERE id = ? AND status = 'active' "
                    "AND (total_price - deposit_paid - amount_paid) <= 0 "
                    "AND EXISTS (SELECT 1 FROM payments WHERE mpesa_receipt_number = ? AND plan_id = ?)",
                    [stk["plan_id"], receipt_str, stk["plan_id"]],
                ),
                (
                    "UPDATE mpesa_stk_requests SET status = 'completed', processed_at = ? "
                    "WHERE id = ? AND status = 'pending' "
                    "AND EXISTS (SELECT 1 FROM payments WHERE mpesa_receipt_number = ? AND plan_id = ?)",
                    [now, stk["id"], receipt_str, stk["plan_id"]],
                ),
            ])
        except Exception as exc:
            # Unique constraint violation or transient D1 failure: treat as safe no-op/retry.
            _log_mpesa_callback(
                "batch_error", checkout=checkout_masked, error_type=type(exc).__name__
            )
            return json_response(_callback_ack())

        def _changes(res):
            if not isinstance(res, dict):
                return None
            meta = res.get("meta") or {}
            if isinstance(meta, dict):
                for key in ("changes", "rows_written", "changed_db_rows"):
                    if key in meta and meta[key] is not None:
                        try:
                            return int(meta[key])
                        except (TypeError, ValueError):
                            return None
            return None

        insert_changes = _changes(batch_results[0]) if isinstance(batch_results, list) and batch_results else None
        if insert_changes == 0:
            # Guard prevented credit (race, replay, or balance changed) — idempotent ack.
            await d1.batch([
                (
                    "UPDATE mpesa_stk_requests SET status = 'completed', processed_at = ? "
                    "WHERE id = ? AND status = 'pending' "
                    "AND EXISTS (SELECT 1 FROM payments WHERE mpesa_transaction_id = ?)",
                    [now, stk["id"], checkout_request_id],
                )
            ])
            _log_mpesa_callback("noop", reason="guard_prevented_credit", checkout=checkout_masked)
            return json_response(_callback_ack())

        _log_mpesa_callback("accepted", checkout=checkout_masked)
        return json_response(_callback_ack())
    except Exception as exc:
        _log_mpesa_callback("error", error_type=type(exc).__name__)
        return json_response(_callback_ack())
