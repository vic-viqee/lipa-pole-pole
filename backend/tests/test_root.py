import os
import unittest

from fastapi.testclient import TestClient


os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("MPESA_CONSUMER_KEY", "dummy")
os.environ.setdefault("MPESA_CONSUMER_SECRET", "dummy")
os.environ.setdefault("MPESA_SHORTCODE", "123456")
os.environ.setdefault("MPESA_PASSKEY", "dummy")
os.environ.setdefault("MPESA_CALLBACK_URL", "https://example.com/callback")

from app.main import app


class RootHealthTest(unittest.TestCase):
    def test_root_health_endpoint(self):
        client = TestClient(app)
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Lipa Polepole API is running"})


if __name__ == "__main__":
    unittest.main()
