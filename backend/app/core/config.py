from __future__ import annotations

import os
from typing import Literal

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

        ENV: Literal["development", "production", "testing"] = "production"
        DATABASE_URL: str = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://nazorat:change_me_in_prod@localhost:5432/nazorat",
        )
        DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
        DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))

        TZ_LOCAL: str = os.getenv("TZ_LOCAL", "Asia/Tashkent")
        NO_DATA_MINUTES: int = int(os.getenv("NO_DATA_MINUTES", "45"))
        CONSECUTIVE_WINDOWS: int = int(os.getenv("CONSECUTIVE_WINDOWS", "3"))
        ALERT_COOLDOWN_HOURS: int = int(os.getenv("ALERT_COOLDOWN_HOURS", "6"))
        PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:5174")

        JWT_SECRET: str = os.getenv(
            "JWT_SECRET", "change_me_32_bytes_min_super_secret_nazorat_prod_key"
        )
        JWT_ALG: str = os.getenv("JWT_ALG", "HS256")
        ACCESS_TOKEN_TTL_MIN: int = int(os.getenv("ACCESS_TOKEN_TTL_MIN", "60"))
        REFRESH_TOKEN_TTL_DAYS: int = int(os.getenv("REFRESH_TOKEN_TTL_DAYS", "30"))

except ImportError:

    class Settings:  # type: ignore[no-redef]
        ENV: str = "production"
        DATABASE_URL: str = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://nazorat:change_me_in_prod@localhost:5432/nazorat",
        )
        DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
        DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))

        TZ_LOCAL: str = os.getenv("TZ_LOCAL", "Asia/Tashkent")
        NO_DATA_MINUTES: int = int(os.getenv("NO_DATA_MINUTES", "45"))
        CONSECUTIVE_WINDOWS: int = int(os.getenv("CONSECUTIVE_WINDOWS", "3"))
        ALERT_COOLDOWN_HOURS: int = int(os.getenv("ALERT_COOLDOWN_HOURS", "6"))
        PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:5174")

        JWT_SECRET: str = os.getenv(
            "JWT_SECRET", "change_me_32_bytes_min_super_secret_nazorat_prod_key"
        )
        JWT_ALG: str = os.getenv("JWT_ALG", "HS256")
        ACCESS_TOKEN_TTL_MIN: int = int(os.getenv("ACCESS_TOKEN_TTL_MIN", "60"))
        REFRESH_TOKEN_TTL_DAYS: int = int(os.getenv("REFRESH_TOKEN_TTL_DAYS", "30"))


settings = Settings()
