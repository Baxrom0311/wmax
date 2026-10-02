import pytest
from app.core.config import (
    InsecureConfigurationError,
    Settings,
    validate_production_settings,
)


def _valid_production_realtime(cfg: Settings) -> None:
    cfg.REALTIME_TRANSPORT = "redis_streams"
    cfg.REDIS_URL = "redis://localhost:6379/0"


def test_production_refuses_placeholder_jwt_secret():
    cfg = Settings()
    cfg.ENV = "production"
    cfg.JWT_SECRET = "change_me_32_bytes_min"
    cfg.DATABASE_URL = "postgresql+asyncpg://wmax:real_pass@localhost:5432/wmax"
    cfg.ENABLE_DEMO_ACCOUNTS = False
    cfg.INGEST_API_KEY = "valid_hex_key_for_testing"
    cfg.SMS_PROVIDER = "eskiz"
    _valid_production_realtime(cfg)

    with pytest.raises(InsecureConfigurationError, match="JWT_SECRET is still"):
        validate_production_settings(cfg)


def test_production_refuses_short_jwt_secret():
    cfg = Settings()
    cfg.ENV = "production"
    cfg.JWT_SECRET = "short"
    cfg.DATABASE_URL = "postgresql+asyncpg://wmax:real_pass@localhost:5432/wmax"
    cfg.ENABLE_DEMO_ACCOUNTS = False
    cfg.INGEST_API_KEY = "valid_hex_key_for_testing"
    cfg.SMS_PROVIDER = "eskiz"
    _valid_production_realtime(cfg)

    with pytest.raises(InsecureConfigurationError, match="must be at least 32 characters"):
        validate_production_settings(cfg)


def test_production_refuses_missing_ingest_key():
    cfg = Settings()
    cfg.ENV = "production"
    cfg.JWT_SECRET = "a" * 32
    cfg.DATABASE_URL = "postgresql+asyncpg://wmax:real_pass@localhost:5432/wmax"
    cfg.ENABLE_DEMO_ACCOUNTS = False
    cfg.INGEST_API_KEY = ""
    cfg.SMS_PROVIDER = "eskiz"
    _valid_production_realtime(cfg)

    with pytest.raises(InsecureConfigurationError, match="INGEST_API_KEY is required"):
        validate_production_settings(cfg)


def test_production_refuses_demo_accounts():
    cfg = Settings()
    cfg.ENV = "production"
    cfg.JWT_SECRET = "a" * 32
    cfg.DATABASE_URL = "postgresql+asyncpg://wmax:real_pass@localhost:5432/wmax"
    cfg.ENABLE_DEMO_ACCOUNTS = True
    cfg.INGEST_API_KEY = "valid_key"
    cfg.SMS_PROVIDER = "eskiz"
    _valid_production_realtime(cfg)

    with pytest.raises(InsecureConfigurationError, match="ENABLE_DEMO_ACCOUNTS must be off"):
        validate_production_settings(cfg)


def test_production_refuses_change_me_db_password():
    cfg = Settings()
    cfg.ENV = "production"
    cfg.JWT_SECRET = "a" * 32
    cfg.DATABASE_URL = "postgresql+asyncpg://wmax:change_me_in_prod@localhost:5432/wmax"
    cfg.ENABLE_DEMO_ACCOUNTS = False
    cfg.INGEST_API_KEY = "valid_key"
    cfg.SMS_PROVIDER = "eskiz"
    _valid_production_realtime(cfg)

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


def test_production_refuses_log_sms_provider():
    cfg = Settings()
    cfg.ENV = "production"
    cfg.JWT_SECRET = "a" * 32
    cfg.DATABASE_URL = "postgresql+asyncpg://wmax:real_pass@localhost:5432/wmax"
    cfg.ENABLE_DEMO_ACCOUNTS = False
    cfg.INGEST_API_KEY = "valid_key"
    cfg.SMS_PROVIDER = "log"
    _valid_production_realtime(cfg)

    with pytest.raises(InsecureConfigurationError, match="SMS_PROVIDER must point"):
        validate_production_settings(cfg)


def test_production_refuses_memory_realtime_transport():
    cfg = Settings()
    cfg.ENV = "production"
    cfg.JWT_SECRET = "a" * 32
    cfg.DATABASE_URL = "postgresql+asyncpg://wmax:real_pass@localhost:5432/wmax"
    cfg.ENABLE_DEMO_ACCOUNTS = False
    cfg.INGEST_API_KEY = "valid_key"
    cfg.SMS_PROVIDER = "eskiz"
    cfg.REALTIME_TRANSPORT = "memory"
    cfg.REDIS_URL = ""

    with pytest.raises(InsecureConfigurationError, match="REALTIME_TRANSPORT must be redis_streams"):
        validate_production_settings(cfg)


def test_production_refuses_redis_streams_without_redis_url():
    cfg = Settings()
    cfg.ENV = "production"
    cfg.JWT_SECRET = "a" * 32
    cfg.DATABASE_URL = "postgresql+asyncpg://wmax:real_pass@localhost:5432/wmax"
    cfg.ENABLE_DEMO_ACCOUNTS = False
    cfg.INGEST_API_KEY = "valid_key"
    cfg.SMS_PROVIDER = "eskiz"
    cfg.REALTIME_TRANSPORT = "redis_streams"
    cfg.REDIS_URL = ""

    with pytest.raises(InsecureConfigurationError, match="REDIS_URL is required"):
        validate_production_settings(cfg)
