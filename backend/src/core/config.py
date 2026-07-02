from typing import Any


class Settings:
    def __init__(self, env: dict[str, Any]) -> None:
        self.SECRET_KEY: str = env.get("SECRET_KEY", "")
        self.ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(env.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.MPESA_CONSUMER_KEY: str = env.get("MPESA_CONSUMER_KEY", "")
        self.MPESA_CONSUMER_SECRET: str = env.get("MPESA_CONSUMER_SECRET", "")
        self.MPESA_SHORTCODE: str = env.get("MPESA_SHORTCODE", "")
        self.MPESA_PASSKEY: str = env.get("MPESA_PASSKEY", "")
        self.MPESA_CALLBACK_URL: str = env.get("MPESA_CALLBACK_URL", "")
        self.ENVIRONMENT: str = env.get("ENVIRONMENT", "production")
        self.FRONTEND_URL: str = env.get("FRONTEND_URL", "http://localhost:5173")


settings: Settings | None = None


def get_settings(env: dict[str, Any]) -> Settings:
    global settings
    if settings is None:
        settings = Settings(env)
    return settings
