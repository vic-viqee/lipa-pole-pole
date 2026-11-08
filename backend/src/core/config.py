from typing import Any

_settings: dict[str, Any] | None = None

_MPESA_BASE_URLS = {
    "sandbox": "https://sandbox.safaricom.co.ke",
    "production": "https://api.safaricom.co.ke",
}


def _resolve_mpesa_base_url(env: dict[str, Any]) -> str:
    explicit = (env.get("MPESA_BASE_URL") or "").strip().rstrip("/")
    if explicit:
        return explicit
    env_name = (env.get("MPESA_ENV") or env.get("ENVIRONMENT") or "sandbox").strip().lower()
    return _MPESA_BASE_URLS.get(env_name, _MPESA_BASE_URLS["sandbox"])


def _resolve_allowed_origins(env: dict[str, Any], frontend_url: str) -> list[str]:
    raw = env.get("ALLOWED_ORIGINS")
    if raw and str(raw).strip():
        origins = [o.strip().rstrip("/") for o in str(raw).split(",") if o.strip()]
        return origins or [frontend_url.rstrip("/")]
    return [frontend_url.rstrip("/")]


def init_settings(env: dict[str, Any]) -> None:
    global _settings
    if _settings is None:
        environment = (env.get("ENVIRONMENT") or "production").strip().lower()
        secret_key = env.get("SECRET_KEY", "")
        if environment == "production" and not str(secret_key).strip():
            raise RuntimeError("SECRET_KEY is required in production")
        if not str(secret_key).strip():
            secret_key = "dev-insecure-secret-key"
        mpesa_env = (env.get("MPESA_ENV") or "sandbox").strip().lower()
        frontend_url = (env.get("FRONTEND_URL") or "http://localhost:5173").strip().rstrip("/")
        _settings = {
            "SECRET_KEY": secret_key,
            "ALGORITHM": "HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": int(env.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            "MPESA_CONSUMER_KEY": env.get("MPESA_CONSUMER_KEY", ""),
            "MPESA_CONSUMER_SECRET": env.get("MPESA_CONSUMER_SECRET", ""),
            "MPESA_SHORTCODE": env.get("MPESA_SHORTCODE", ""),
            "MPESA_PASSKEY": env.get("MPESA_PASSKEY", ""),
            "MPESA_CALLBACK_URL": env.get("MPESA_CALLBACK_URL", ""),
            "MPESA_ENV": mpesa_env,
            "MPESA_BASE_URL": _resolve_mpesa_base_url(env),
            "MPESA_TIMEOUT_SECONDS": int(env.get("MPESA_TIMEOUT_SECONDS", "15")),
            "MPESA_TOKEN_REFRESH_SKEW_SECONDS": int(env.get("MPESA_TOKEN_REFRESH_SKEW_SECONDS", "60")),
            "ENVIRONMENT": environment,
            "FRONTEND_URL": frontend_url,
            "ALLOWED_ORIGINS": _resolve_allowed_origins(env, frontend_url),
        }


def get_settings() -> dict[str, Any]:
    assert _settings is not None, "Settings not initialized"
    return _settings
