import pytest
from app.core.config import (
    InsecureConfigurationError,
    Settings,
    validate_production_settings,
)


def test_production_refuses_placeholder_jwt_secret():
    cfg = Settings()
    cfg.ENV = "production"
    cfg.JWT_SECRET = "change_me_32_bytes_min"
    cfg.DATABASE_URL = "postgresql+asyncpg://wmax:real_pass@localhost:5432/wmax"
    cfg.ENABLE_DEMO_ACCOUNTS = False
    cfg.INGEST_API_KEY = "valid_hex_key_for_testing"

    with pytest.raises(InsecureConfigurationError, match="JWT_SECRET is still"):
        validate_production_settings(cfg)


def test_production_refuses_short_jwt_secret():
    cfg = Settings()
    cfg.ENV = "production"
    cfg.JWT_SECRET = "short"
    cfg.DATABASE_URL = "postgresql+asyncpg://wmax:real_pass@localhost:5432/wmax"
    cfg.ENABLE_DEMO_ACCOUNTS = False
    cfg.INGEST_API_KEY = "valid_hex_key_for_testing"

    with pytest.raises(InsecureConfigurationError, match="must be at least 32 characters"):
        validate_production_settings(cfg)


def test_production_refuses_missing_ingest_key():
    cfg = Settings()
    cfg.ENV = "production"
    cfg.JWT_SECRET = "a" * 32
    cfg.DATABASE_URL = "postgresql+asyncpg://wmax:real_pass@localhost:5432/wmax"
    cfg.ENABLE_DEMO_ACCOUNTS = False
    cfg.INGEST_API_KEY = ""

    with pytest.raises(InsecureConfigurationError, match="INGEST_API_KEY is required"):
        validate_production_settings(cfg)


def test_production_refuses_demo_accounts():
    cfg = Settings()
    cfg.ENV = "production"
    cfg.JWT_SECRET = "a" * 32
    cfg.DATABASE_URL = "postgresql+asyncpg://wmax:real_pass@localhost:5432/wmax"
    cfg.ENABLE_DEMO_ACCOUNTS = True
    cfg.INGEST_API_KEY = "valid_key"

    with pytest.raises(InsecureConfigurationError, match="ENABLE_DEMO_ACCOUNTS must be off"):
        validate_production_settings(cfg)


def test_production_refuses_change_me_db_password():
    cfg = Settings()
    cfg.ENV = "production"
    cfg.JWT_SECRET = "a" * 32
    cfg.DATABASE_URL = "postgresql+asyncpg://wmax:change_me_in_prod@localhost:5432/wmax"
    cfg.ENABLE_DEMO_ACCOUNTS = False
    cfg.INGEST_API_KEY = "valid_key"

    with pytest.raises(InsecureConfigurationError, match="DATABASE_URL still contains"):
        validate_production_settings(cfg)


def test_non_production_skips_validation():
    cfg = Settings()
    cfg.ENV = "development"
    cfg.JWT_SECRET = "change_me_32_bytes_min"
    cfg.DATABASE_URL = "postgresql+asyncpg://wmax:change_me_in_prod@localhost:5432/wmax"
    cfg.ENABLE_DEMO_ACCOUNTS = True
    cfg.INGEST_API_KEY = ""

    # Should not raise
    validate_production_settings(cfg)
