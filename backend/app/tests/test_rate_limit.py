import pytest
from fastapi import HTTPException
from app.core.rate_limit import SlidingWindowRateLimiter, enforce_login_rate_limit


def test_sliding_window_blocks_after_max_attempts():
    limiter = SlidingWindowRateLimiter(max_attempts=3, window_seconds=10, redis_url=None)
    key = "user_test_1"

    assert limiter.check(key) == 0
    assert limiter.check(key) == 0
    assert limiter.check(key) == 0

    # 4th attempt should be blocked
    wait = limiter.check(key)
    assert wait > 0
    assert wait <= 10


def test_reset_clears_limiter_bucket():
    limiter = SlidingWindowRateLimiter(max_attempts=2, window_seconds=10, redis_url=None)
    key = "user_test_2"

    assert limiter.check(key) == 0
    assert limiter.check(key) == 0
    assert limiter.check(key) > 0

    limiter.reset(key)
    assert limiter.check(key) == 0


def test_enforce_login_rate_limit_raises_429():
    from app.core.rate_limit import login_limiter
    login_limiter.clear()

    key = "test_ip_phone_combo"
    for _ in range(login_limiter.max_attempts):
        login_limiter.check(key)

    with pytest.raises(HTTPException) as exc_info:
        enforce_login_rate_limit(key)

    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers
    assert int(exc_info.value.headers["Retry-After"]) > 0
