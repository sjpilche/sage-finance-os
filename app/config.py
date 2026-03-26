"""
Sage Finance OS — application configuration.

Single source of truth for all settings. Reads from environment variables
with sensible defaults for local development.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Environment ──────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Database (async — API layer) ─────────────────────────────
    DATABASE_URL: str = "postgresql://sage:sage@localhost:5432/sage_finance"
    DB_POOL_MIN: int = 5
    DB_POOL_MAX: int = 20
    DB_COMMAND_TIMEOUT: int = 300

    # ── Database (sync — pipeline layer) ─────────────────────────
    DATABASE_URL_SYNC: str = "postgresql://sage:sage@localhost:5432/sage_finance"
    DB_SYNC_POOL_MIN: int = 2
    DB_SYNC_POOL_MAX: int = 10

    # ── API ──────────────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8090
    API_KEY: str = "dev-api-key"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3004"

    # ── Auth ─────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "dev-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Sage Intacct (defaults empty — configured per-connection) ─
    SAGE_INTACCT_SENDER_ID: str = ""
    SAGE_INTACCT_SENDER_PASSWORD: str = ""
    SAGE_INTACCT_COMPANY_ID: str = ""
    SAGE_INTACCT_USER_ID: str = ""
    SAGE_INTACCT_USER_PASSWORD: str = ""

    # ── Rate Limiting ────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 100

    # ── Migrations ───────────────────────────────────────────────
    RUN_MIGRATIONS: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def validate_production(self) -> None:
        """Refuse to start in production with default secrets."""
        if self.ENVIRONMENT != "production":
            return
        defaults = {
            "API_KEY": "dev-api-key",
            "JWT_SECRET_KEY": "dev-jwt-secret-change-in-production",
        }
        for key, default_val in defaults.items():
            if getattr(self, key) == default_val:
                raise ValueError(
                    f"{key} still has its default value. "
                    f"Set a real value for production deployment."
                )


_settings: Settings | None = None


def get_settings() -> Settings:
    """Singleton settings accessor."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
