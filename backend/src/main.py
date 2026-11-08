from typing import Any

from workers import WorkerEntrypoint, Request, Response
from workers import Response as Resp

from app import handle_request
from core.config import init_settings
from core.router import HTTPException, json_response, _cors_headers


class Default(WorkerEntrypoint):
    async def on_fetch(self, request: Request) -> Response:
        env: dict[str, Any] = {
            "DB": self.env.DB,
        }
        for key in (
            "SECRET_KEY",
            "ENVIRONMENT",
            "FRONTEND_URL",
            "ALLOWED_ORIGINS",
            "MPESA_ENV",
            "MPESA_BASE_URL",
            "MPESA_TIMEOUT_SECONDS",
            "MPESA_TOKEN_REFRESH_SKEW_SECONDS",
            "MPESA_CONSUMER_KEY",
            "MPESA_CONSUMER_SECRET",
            "MPESA_SHORTCODE",
            "MPESA_PASSKEY",
            "MPESA_CALLBACK_URL",
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "ASSETS",
        ):
            val = getattr(self.env, key, None)
            if val is not None:
                env[key] = val

        init_settings(env)

        if str(request.method).upper() == "OPTIONS":
            origin = request.headers.get("Origin") if hasattr(request, "headers") else None
            return Resp("", status=204, headers=_cors_headers(origin))

        try:
            return await handle_request(request, env)
        except HTTPException as e:
            origin = request.headers.get("Origin") if hasattr(request, "headers") else None
            return json_response({"detail": e.detail}, status=e.status_code, origin=origin)
        except Exception as e:
            print(f"[unhandled_error] type={type(e).__name__}")
            origin = request.headers.get("Origin") if hasattr(request, "headers") else None
            return json_response({"detail": "Internal server error"}, status=500, origin=origin)
