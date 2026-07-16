from collections.abc import Callable
from typing import Any

from asgi import ASGI

from src.app import app


class EnvInjector:
    def __init__(self, env: dict[str, Any]) -> None:
        self.env = env

    async def __call__(
        self, scope: dict[str, Any], receive: Callable, send: Callable
    ) -> None:
        if scope["type"] == "http":
            scope["env"] = self.env
        await app(scope, receive, send)


class LipaPolepole(WorkerEntryPoint):
    def fetch(self, request: Request) -> Response:
        env = {"DB": self.env.DB}
        for key in (
            "SECRET_KEY",
            "ENVIRONMENT",
            "FRONTEND_URL",
            "MPESA_CONSUMER_KEY",
            "MPESA_CONSUMER_SECRET",
            "MPESA_SHORTCODE",
            "MPESA_PASSKEY",
            "MPESA_CALLBACK_URL",
            "ACCESS_TOKEN_EXPIRE_MINUTES",
        ):
            val = getattr(self.env, key, None)
            if val is not None:
                env[key] = val

        return ASGI(EnvInjector(env)).fetch(request)
