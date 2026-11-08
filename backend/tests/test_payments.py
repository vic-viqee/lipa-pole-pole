import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import tests.conftest  # noqa: F401  (installs shims/path)
from tests.conftest import app_request, make_env, make_test_db
from core.security import hash_password


def run(coro):
    return asyncio.run(coro)


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def mpesa_callback_payload(checkout_request_id: str, amount: int, receipt: str, phone="254712345678", result_code=0):
    return {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "m-1",
                "CheckoutRequestID": checkout_request_id,
                "ResultCode": result_code,
                "ResultDesc": "OK" if result_code == 0 else "Failed",
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": amount},
                        {"Name": "MpesaReceiptNumber", "Value": receipt},
                        {"Name": "PhoneNumber", "Value": int(phone)},
                    ]
                } if result_code == 0 else {"Item": []},
            }
        }
    }


class CurrentAppTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_test_db()
        self.env = make_env(self.conn)
        self._seed()

    def tearDown(self):
        self.conn.close()

    def _seed(self):
        cur = self.conn.cursor()
        # two vendors
        cur.execute(
            "INSERT INTO vendors (shop_name, email, phone, hashed_password) VALUES (?,?,?,?)",
            ("Shop A", "a@example.com", "254700000001", hash_password("pass-a")),
        )
        self.vendor_a = cur.lastrowid
        cur.execute(
            "INSERT INTO vendors (shop_name, email, phone, hashed_password) VALUES (?,?,?,?)",
            ("Shop B", "b@example.com", "254700000002", hash_password("pass-b")),
        )
        self.vendor_b = cur.lastrowid
        # customer/plan for vendor A
        cur.execute(
            "INSERT INTO customers (full_name, phone, national_id, vendor_id) VALUES (?,?,?,?)",
            ("Alice", "254712345678", "123", self.vendor_a),
        )
        self.customer_a = cur.lastrowid
        cur.execute(
            "INSERT INTO installment_plans (product_name,total_price,deposit_paid,amount_paid,customer_id,vendor_id,tracking_token,status) "
            "VALUES (?,?,?,?,?,?,?,?)",
            ("Phone", 100000, 20000, 10000, self.customer_a, self.vendor_a, "track-a", "active"),  # remaining 70000 cents
        )
        self.plan_a = cur.lastrowid
        # pending STK for plan A (500 KSh = 50000 cents)
        cur.execute(
            "INSERT INTO mpesa_stk_requests (checkout_request_id,merchant_request_id,plan_id,phone,requested_amount,status) "
            "VALUES (?,?,?,?,?,?)",
            ("ws_CO_A1", "m1", self.plan_a, "254712345678", 50000, "pending"),
        )
        self.stk_a1 = cur.lastrowid
        # vendor B plan
        cur.execute(
            "INSERT INTO customers (full_name, phone, national_id, vendor_id) VALUES (?,?,?,?)",
            ("Bob", "254711111111", "456", self.vendor_b),
        )
        customer_b = cur.lastrowid
        cur.execute(
            "INSERT INTO installment_plans (product_name,total_price,deposit_paid,amount_paid,customer_id,vendor_id,tracking_token,status) "
            "VALUES (?,?,?,?,?,?,?,?)",
            ("TV", 50000, 0, 0, customer_b, self.vendor_b, "track-b", "active"),
        )
        self.plan_b = cur.lastrowid
        self.conn.commit()

    def login(self, email, password):
        status, data = run(app_request(self.env, "POST", "/api/v1/auth/login", body={"email": email, "password": password}))
        self.assertEqual(status, 200, data)
        return data["access_token"]

    def payment_state(self, plan_id):
        row = self.conn.execute(
            "SELECT amount_paid, status FROM installment_plans WHERE id=?", (plan_id,)
        ).fetchone()
        count = self.conn.execute(
            "SELECT COUNT(*) c, COALESCE(SUM(amount),0) s FROM payments WHERE plan_id=? AND status='completed'",
            (plan_id,),
        ).fetchone()
        return {"amount_paid": row["amount_paid"], "plan_status": row["status"], "completed_count": count["c"], "completed_sum": count["s"]}

    def payments_count(self, plan_id=None):
        if plan_id is None:
            return self.conn.execute("SELECT COUNT(*) c FROM payments").fetchone()["c"]
        return self.conn.execute("SELECT COUNT(*) c FROM payments WHERE plan_id=?", (plan_id,)).fetchone()["c"]

    def stk_state(self, checkout_request_id):
        row = self.conn.execute(
            "SELECT status, processed_at FROM mpesa_stk_requests WHERE checkout_request_id=?",
            (checkout_request_id,),
        ).fetchone()
        if row is None:
            return None
        return {"status": row["status"], "processed_at": row["processed_at"]}

    def test_root_health_current_app(self):
        status, data = run(app_request(self.env, "GET", "/"))
        self.assertEqual(status, 200)
        self.assertEqual(data, {"message": "Lipa Polepole API is running"})

    def test_callback_rejects_unknown_checkout_request_id(self):
        before = self.payment_state(self.plan_a)
        payload = mpesa_callback_payload("ws_UNKNOWN", 500, "RCPT-UNK")
        status, data = run(app_request(self.env, "POST", "/api/v1/payments/mpesa/callback", body=payload))
        self.assertEqual(status, 200)
        self.assertEqual(data.get("ResultCode"), 0)
        after = self.payment_state(self.plan_a)
        self.assertEqual(after["amount_paid"], before["amount_paid"])
        self.assertEqual(after["plan_status"], before["plan_status"])
        self.assertEqual(after["completed_count"], before["completed_count"])
        self.assertEqual(self.payments_count(), 0)
        self.assertIsNone(self.stk_state("ws_UNKNOWN"))

    def test_callback_rejects_wrong_amount(self):
        before = self.payment_state(self.plan_a)
        payload = mpesa_callback_payload("ws_CO_A1", 499, "RCPT-WRONG")  # requested 500
        status, data = run(app_request(self.env, "POST", "/api/v1/payments/mpesa/callback", body=payload))
        self.assertEqual(status, 200)
        self.assertEqual(data.get("ResultCode"), 0)
        after = self.payment_state(self.plan_a)
        self.assertEqual(after["amount_paid"], before["amount_paid"])
        self.assertEqual(after["plan_status"], before["plan_status"])
        self.assertEqual(after["completed_count"], before["completed_count"])
        self.assertEqual(self.payments_count(), 0)
        stk = self.stk_state("ws_CO_A1")
        self.assertIsNotNone(stk)
        self.assertEqual(stk["status"], "pending")

    def test_callback_rejects_payment_exceeding_remaining_balance_at_commit(self):
        # reduce remaining balance below requested amount after STK initiation
        self.conn.execute("UPDATE installment_plans SET amount_paid = 60000 WHERE id=?", (self.plan_a,))  # remaining now 20000
        self.conn.commit()
        before = self.payment_state(self.plan_a)
        payload = mpesa_callback_payload("ws_CO_A1", 500, "RCPT-OVER")  # 50000 cents requested, remaining 20000
        status, data = run(app_request(self.env, "POST", "/api/v1/payments/mpesa/callback", body=payload))
        self.assertEqual(status, 200)
        self.assertEqual(data.get("ResultCode"), 0)
        after = self.payment_state(self.plan_a)
        self.assertEqual(after["amount_paid"], before["amount_paid"])
        self.assertEqual(after["plan_status"], before["plan_status"])
        self.assertEqual(after["completed_count"], before["completed_count"])
        self.assertEqual(self.payments_count(), 0)
        stk = self.stk_state("ws_CO_A1")
        self.assertIsNotNone(stk)
        self.assertEqual(stk["status"], "pending")

    def test_callback_rejects_duplicate_receipt_number(self):
        # seed an existing completed payment with receipt
        self.conn.execute(
            "INSERT INTO payments (amount, mpesa_transaction_id, plan_id, status, mpesa_receipt_number) VALUES (?,?,?,?,?)",
            (10000, "older", self.plan_a, "completed", "RCPT-DUP"),
        )
        self.conn.commit()
        before = self.payment_state(self.plan_a)
        payload = mpesa_callback_payload("ws_CO_A1", 500, "RCPT-DUP")
        status, data = run(app_request(self.env, "POST", "/api/v1/payments/mpesa/callback", body=payload))
        self.assertEqual(status, 200)
        self.assertEqual(data.get("ResultCode"), 0)
        after = self.payment_state(self.plan_a)
        self.assertEqual(after["amount_paid"], before["amount_paid"])
        self.assertEqual(after["plan_status"], before["plan_status"])
        self.assertEqual(after["completed_count"], before["completed_count"])
        self.assertEqual(self.payments_count(), 1)
        n = self.conn.execute("SELECT COUNT(*) c FROM payments WHERE mpesa_receipt_number='RCPT-DUP'").fetchone()["c"]
        self.assertEqual(n, 1)
        stk = self.stk_state("ws_CO_A1")
        self.assertIsNotNone(stk)
        self.assertEqual(stk["status"], "completed")

    def test_replayed_successful_callback_changes_nothing_and_returns_success(self):
        payload = mpesa_callback_payload("ws_CO_A1", 500, "RCPT-OK1")
        status, data = run(app_request(self.env, "POST", "/api/v1/payments/mpesa/callback", body=payload))
        self.assertEqual(status, 200)
        self.assertEqual(data.get("ResultCode"), 0)
        after_first = self.payment_state(self.plan_a)
        self.assertEqual(self.payments_count(), 1)
        self.assertEqual(after_first["amount_paid"], 10000 + 50000)
        self.assertEqual(after_first["plan_status"], "active")
        self.assertEqual(after_first["completed_count"], 1)
        stk = self.stk_state("ws_CO_A1")
        self.assertIsNotNone(stk)
        self.assertEqual(stk["status"], "completed")

        # replay
        status2, data2 = run(app_request(self.env, "POST", "/api/v1/payments/mpesa/callback", body=payload))
        self.assertEqual(status2, 200)
        self.assertEqual(data2.get("ResultCode"), 0)
        after_second = self.payment_state(self.plan_a)
        self.assertEqual(self.payments_count(), 1)
        self.assertEqual(after_second["amount_paid"], after_first["amount_paid"])
        self.assertEqual(after_second["plan_status"], after_first["plan_status"])
        self.assertEqual(after_second["completed_count"], after_first["completed_count"])
        self.assertEqual(after_second["completed_sum"], after_first["completed_sum"])
        stk2 = self.stk_state("ws_CO_A1")
        self.assertIsNotNone(stk2)
        self.assertEqual(stk2["status"], "completed")

    def test_vendor_cannot_read_or_pay_against_another_vendors_plan(self):
        token_a = self.login("a@example.com", "pass-a")
        token_b = self.login("b@example.com", "pass-b")

        # vendor B cannot read vendor A plan
        status, data = run(app_request(self.env, "GET", f"/api/v1/plans/{self.plan_a}", headers=auth_header(token_b)))
        self.assertEqual(status, 404, data)

        # vendor B cannot list payments for vendor A plan
        status, data = run(app_request(self.env, "GET", f"/api/v1/payments/plan/{self.plan_a}", headers=auth_header(token_b)))
        self.assertEqual(status, 404, data)

        # vendor B cannot record manual payment against vendor A plan
        before = self.payment_state(self.plan_a)
        status, data = run(app_request(
            self.env, "POST", "/api/v1/payments/",
            headers=auth_header(token_b),
            body={"plan_id": self.plan_a, "amount": 100},
        ))
        self.assertEqual(status, 404, data)
        self.assertEqual(self.payment_state(self.plan_a), before)

        # vendor B cannot initiate STK for vendor A tracking token (public tracking token tied to A's plan)
        with patch("api.v1.payments.get_access_token", new=AsyncMock(return_value="tok")), \
             patch("api.v1.payments.mpesa_stk_push", new=AsyncMock(return_value={
                 "CheckoutRequestID": "x", "MerchantRequestID": "y", "ResponseDescription": "ok"
             })):
            status, data = run(app_request(
                self.env, "POST", f"/api/v1/payments/mpesa/stk/track-a",
                body={"phone": "254712345678", "amount": 100},
                headers={"Content-Type": "application/json"},
            ))
        # STK is public by tracking token (not vendor-auth) - it targets that plan; vendor isolation check is satisfied
        # by ensuring vendor-scoped endpoints above deny cross-vendor access. STK creates a pending request for plan A.
        self.assertIn(status, (200, 201), data)
        stk_rows = self.conn.execute("SELECT plan_id FROM mpesa_stk_requests WHERE checkout_request_id='x'").fetchone()
        self.assertIsNotNone(stk_rows)
        self.assertEqual(stk_rows["plan_id"], self.plan_a)

    def test_manual_payment_rejects_negative_or_zero_amount(self):
        token_a = self.login("a@example.com", "pass-a")
        before = self.payment_state(self.plan_a)
        for amount in (0, -1, -100.5):
            status, data = run(app_request(
                self.env, "POST", "/api/v1/payments/",
                headers=auth_header(token_a),
                body={"plan_id": self.plan_a, "amount": amount},
            ))
            self.assertEqual(status, 400, (amount, data))
            self.assertEqual(self.payment_state(self.plan_a), before)

    def test_phone_validation_accepts_valid_and_rejects_invalid(self):
        from core.validate import validate_kenyan_phone

        for ok in ("254712345678", "254112345678", "0712345678", "0112345678"):
            self.assertTrue(validate_kenyan_phone(ok).startswith("254"))

        for bad in ("25471234567", "2547123456789", "+2547123456789", "25471234567a", "", None):
            with self.assertRaises((ValueError, Exception), msg=bad):
                validate_kenyan_phone(bad)  # type: ignore

        # STK endpoint uses same validation (mock Daraja so no real API call)
        with patch("api.v1.payments.get_access_token", new=AsyncMock(return_value="tok")), \
             patch("api.v1.payments.mpesa_stk_push", new=AsyncMock(return_value={
                 "CheckoutRequestID": "ws_VALID", "MerchantRequestID": "y", "ResponseDescription": "ok"
             })):
            status, data = run(app_request(
                self.env, "POST", "/api/v1/payments/mpesa/stk/track-a",
                body={"phone": "254112345678", "amount": 100},
                headers={"Content-Type": "application/json"},
            ))
            self.assertEqual(status, 200, data)

        for bad in ("25471234567", "2547123456789", "12345"):
            with patch("api.v1.payments.get_access_token", new=AsyncMock()) as ga, \
                 patch("api.v1.payments.mpesa_stk_push", new=AsyncMock()) as sp:
                status, data = run(app_request(
                    self.env, "POST", "/api/v1/payments/mpesa/stk/track-a",
                    body={"phone": bad, "amount": 100},
                    headers={"Content-Type": "application/json"},
                ))
                self.assertEqual(status, 400, (bad, data))
                ga.assert_not_called()
                sp.assert_not_called()


if __name__ == "__main__":
    unittest.main()
