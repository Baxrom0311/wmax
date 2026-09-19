from __future__ import annotations

import logging
import time

from app.core.exceptions import AIProviderException
from app.core.metrics import ai_circuit_breaker_state

logger = logging.getLogger(__name__)

# Once a provider has failed this many times in a row, stop calling it for a
# while. Clinical requests then fall straight through to the local heuristic
# prognosis instead of each one burning the full retry budget.
BREAKER_FAILURE_THRESHOLD = 5
BREAKER_RESET_SECONDS = 60.0


class CircuitBreakerOpenError(AIProviderException):
    """Raised while the breaker is open so callers fail fast to their fallback."""

    def __init__(self, provider: str) -> None:
        super().__init__(f"{provider} xizmati vaqtincha mavjud emas")


class CircuitBreaker:
    """Process-wide consecutive-failure breaker for one LLM provider."""

    def __init__(self, provider: str) -> None:
        self.provider = provider
        self.failures = 0
        self.opened_at: float | None = None
        ai_circuit_breaker_state.labels(provider=provider).set(0)

    @property
    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if time.monotonic() - self.opened_at >= BREAKER_RESET_SECONDS:
            # Half-open: let one request through to probe recovery.
            self.opened_at = None
            ai_circuit_breaker_state.labels(provider=self.provider).set(0)
            logger.info("%s circuit breaker half-open — probing recovery.", self.provider)
            return False
        return True

    def record_success(self) -> None:
        if self.failures or self.opened_at is not None:
            logger.info("%s circuit breaker closed after a successful call.", self.provider)
        self.failures = 0
        self.opened_at = None
        ai_circuit_breaker_state.labels(provider=self.provider).set(0)

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= BREAKER_FAILURE_THRESHOLD and self.opened_at is None:
            self.opened_at = time.monotonic()
            ai_circuit_breaker_state.labels(provider=self.provider).set(1)
            logger.error(
                "%s circuit breaker OPEN after %d consecutive failures.",
                self.provider,
                self.failures,
            )

    def raise_if_open(self) -> None:
        if self.is_open:
            raise CircuitBreakerOpenError(self.provider)
