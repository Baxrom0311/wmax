from __future__ import annotations

import os
from typing import Literal

# Insecure placeholder values that must never reach a production deployment.
INSECURE_JWT_SECRETS = {
    "change_me_32_bytes_min",
    "change_me_32_bytes_min_super_secret_wmax_prod_key",
}
DEFAULT_JWT_SECRET = "change_me_32_bytes_min_super_secret_wmax_prod_key"
MIN_JWT_SECRET_LENGTH = 32


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def split_origins(raw: str) -> list[str]:
    """Splits a comma-separated CORS origin list into individual origins."""
    return [item.strip() for item in raw.split(",") if item.strip()]


# Single source of truth for defaults, shared by both Settings implementations
# below so the pydantic and the plain-object variant can never drift apart.
_DEFAULTS: dict[str, object] = {
    "ENV": os.getenv("ENV", "production"),
    "DATABASE_URL": os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://wmax:change_me_in_prod@localhost:5432/wmax",
    ),
    "DB_POOL_SIZE": int(os.getenv("DB_POOL_SIZE", "20")),
    "DB_MAX_OVERFLOW": int(os.getenv("DB_MAX_OVERFLOW", "10")),
    "DB_POOL_TIMEOUT": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    "DB_POOL_RECYCLE": int(os.getenv("DB_POOL_RECYCLE", "1800")),
    "TZ_LOCAL": os.getenv("TZ_LOCAL", "Asia/Tashkent"),
    "NO_DATA_MINUTES": int(os.getenv("NO_DATA_MINUTES", "45")),
    "CONSECUTIVE_WINDOWS": int(os.getenv("CONSECUTIVE_WINDOWS", "3")),
    "ALERT_COOLDOWN_HOURS": int(os.getenv("ALERT_COOLDOWN_HOURS", "6")),
    "PUBLIC_BASE_URL": os.getenv("PUBLIC_BASE_URL", "http://localhost:5174"),
    "JWT_SECRET": os.getenv("JWT_SECRET", DEFAULT_JWT_SECRET),
    "JWT_ALG": os.getenv("JWT_ALG", "HS256"),
    "ACCESS_TOKEN_TTL_MIN": int(os.getenv("ACCESS_TOKEN_TTL_MIN", "60")),
    "REFRESH_TOKEN_TTL_DAYS": int(os.getenv("REFRESH_TOKEN_TTL_DAYS", "30")),
    # ── Security controls ────────────────────────────────────────────────────
    # Built-in demo logins are a convenience for local work and the hackathon
    # demo; they are an authentication bypass anywhere else.
    "ENABLE_DEMO_ACCOUNTS": _env_bool("ENABLE_DEMO_ACCOUNTS", False),
    # Shared secret the watch companion app sends on /api/v1/ingest.
    "INGEST_API_KEY": os.getenv("INGEST_API_KEY", ""),
    "CORS_ORIGINS": os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5174,"
        "http://127.0.0.1:5173,http://127.0.0.1:5174",
    ),
    "LOGIN_RATE_LIMIT_ATTEMPTS": int(os.getenv("LOGIN_RATE_LIMIT_ATTEMPTS", "8")),
    "LOGIN_RATE_LIMIT_WINDOW_SEC": int(os.getenv("LOGIN_RATE_LIMIT_WINDOW_SEC", "300")),
    # Caregiver deep-link tokens expire and can be rotated.
    "RELATIVE_TOKEN_TTL_DAYS": int(os.getenv("RELATIVE_TOKEN_TTL_DAYS", "90")),
    # ── Background workers ───────────────────────────────────────────────────
    # Workers live inside the API process. Only one replica may run them, which
    # is enforced with a Postgres advisory lock; this switch turns them off
    # entirely (tests, or a deployment that runs them in a dedicated service).
    "ENABLE_WORKERS": _env_bool("ENABLE_WORKERS", os.getenv("ENV", "production") != "testing"),
    "WORKER_LOCK_ID": int(os.getenv("WORKER_LOCK_ID", "874113001")),
    # ── Outbound notifications ───────────────────────────────────────────────
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    # ── AI assistant ─────────────────────────────────────────────────────────
    # Which LLM backs the clinical prognosis and the Telegram assistant.
    # "deepseek" | "gemini"
    "AI_PROVIDER": os.getenv("AI_PROVIDER", "deepseek"),
    "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY", ""),
    # deepseek-chat (V3, tez) | deepseek-reasoner (R1, chuqurroq, sekinroq)
    "DEEPSEEK_MODEL": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    "DEEPSEEK_BASE_URL": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    # Read by GeminiProvider. An empty key is valid: the clinical service then
    # falls back to its local heuristic prognosis.
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
    "GEMINI_MODEL": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
}

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

        ENV: Literal["development", "production", "testing"] = _DEFAULTS["ENV"]  # type: ignore[assignment]
        DATABASE_URL: str = _DEFAULTS["DATABASE_URL"]  # type: ignore[assignment]
        DB_POOL_SIZE: int = _DEFAULTS["DB_POOL_SIZE"]  # type: ignore[assignment]
        DB_MAX_OVERFLOW: int = _DEFAULTS["DB_MAX_OVERFLOW"]  # type: ignore[assignment]
        DB_POOL_TIMEOUT: int = _DEFAULTS["DB_POOL_TIMEOUT"]  # type: ignore[assignment]
        DB_POOL_RECYCLE: int = _DEFAULTS["DB_POOL_RECYCLE"]  # type: ignore[assignment]

        TZ_LOCAL: str = _DEFAULTS["TZ_LOCAL"]  # type: ignore[assignment]
        NO_DATA_MINUTES: int = _DEFAULTS["NO_DATA_MINUTES"]  # type: ignore[assignment]
        CONSECUTIVE_WINDOWS: int = _DEFAULTS["CONSECUTIVE_WINDOWS"]  # type: ignore[assignment]
        ALERT_COOLDOWN_HOURS: int = _DEFAULTS["ALERT_COOLDOWN_HOURS"]  # type: ignore[assignment]
        PUBLIC_BASE_URL: str = _DEFAULTS["PUBLIC_BASE_URL"]  # type: ignore[assignment]

        JWT_SECRET: str = _DEFAULTS["JWT_SECRET"]  # type: ignore[assignment]
        JWT_ALG: str = _DEFAULTS["JWT_ALG"]  # type: ignore[assignment]
        ACCESS_TOKEN_TTL_MIN: int = _DEFAULTS["ACCESS_TOKEN_TTL_MIN"]  # type: ignore[assignment]
        REFRESH_TOKEN_TTL_DAYS: int = _DEFAULTS["REFRESH_TOKEN_TTL_DAYS"]  # type: ignore[assignment]

        ENABLE_DEMO_ACCOUNTS: bool = _DEFAULTS["ENABLE_DEMO_ACCOUNTS"]  # type: ignore[assignment]
        INGEST_API_KEY: str = _DEFAULTS["INGEST_API_KEY"]  # type: ignore[assignment]
        CORS_ORIGINS: str = _DEFAULTS["CORS_ORIGINS"]  # type: ignore[assignment]
        LOGIN_RATE_LIMIT_ATTEMPTS: int = _DEFAULTS["LOGIN_RATE_LIMIT_ATTEMPTS"]  # type: ignore[assignment]
        LOGIN_RATE_LIMIT_WINDOW_SEC: int = _DEFAULTS["LOGIN_RATE_LIMIT_WINDOW_SEC"]  # type: ignore[assignment]
        RELATIVE_TOKEN_TTL_DAYS: int = _DEFAULTS["RELATIVE_TOKEN_TTL_DAYS"]  # type: ignore[assignment]
        ENABLE_WORKERS: bool = _DEFAULTS["ENABLE_WORKERS"]  # type: ignore[assignment]
        WORKER_LOCK_ID: int = _DEFAULTS["WORKER_LOCK_ID"]  # type: ignore[assignment]

        TELEGRAM_BOT_TOKEN: str = _DEFAULTS["TELEGRAM_BOT_TOKEN"]  # type: ignore[assignment]

        AI_PROVIDER: Literal["deepseek", "gemini"] = _DEFAULTS["AI_PROVIDER"]  # type: ignore[assignment]
        DEEPSEEK_API_KEY: str = _DEFAULTS["DEEPSEEK_API_KEY"]  # type: ignore[assignment]
        DEEPSEEK_MODEL: str = _DEFAULTS["DEEPSEEK_MODEL"]  # type: ignore[assignment]
        DEEPSEEK_BASE_URL: str = _DEFAULTS["DEEPSEEK_BASE_URL"]  # type: ignore[assignment]

        GEMINI_API_KEY: str = _DEFAULTS["GEMINI_API_KEY"]  # type: ignore[assignment]
        GEMINI_MODEL: str = _DEFAULTS["GEMINI_MODEL"]  # type: ignore[assignment]

        @property
        def cors_origins(self) -> list[str]:
            return split_origins(self.CORS_ORIGINS)

except ImportError:

    class Settings:  # type: ignore[no-redef]
        def __init__(self) -> None:
            for key, value in _DEFAULTS.items():
                setattr(self, key, value)

        @property
        def cors_origins(self) -> list[str]:
            return split_origins(self.CORS_ORIGINS)


settings = Settings()


class InsecureConfigurationError(RuntimeError):
    """Raised when a production deployment is missing a mandatory secret."""


def validate_production_settings(cfg: Settings = settings) -> None:
    """Refuses to start a production deployment that still carries demo secrets.

    Called from the application lifespan. Failing loudly at boot is the only way
    a missing JWT_SECRET gets noticed before it signs real clinical sessions.
    """
    if cfg.ENV != "production":
        return

    problems: list[str] = []

    if cfg.JWT_SECRET in INSECURE_JWT_SECRETS:
        problems.append("JWT_SECRET is still the built-in placeholder value")
    if len(cfg.JWT_SECRET) < MIN_JWT_SECRET_LENGTH:
        problems.append(
            f"JWT_SECRET must be at least {MIN_JWT_SECRET_LENGTH} characters"
        )
    if "change_me" in cfg.DATABASE_URL:
        problems.append("DATABASE_URL still contains the placeholder password")
    if cfg.ENABLE_DEMO_ACCOUNTS:
        problems.append("ENABLE_DEMO_ACCOUNTS must be off in production")
    if not cfg.INGEST_API_KEY:
        problems.append("INGEST_API_KEY is required to authenticate device uploads")

    if problems:
        raise InsecureConfigurationError(
            "Refusing to start in production with insecure configuration:\n  - "
            + "\n  - ".join(problems)
        )
