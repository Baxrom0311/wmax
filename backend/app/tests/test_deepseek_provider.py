"""Tests for the DeepSeek LLM provider and the provider factory.

No network: httpx is stubbed so the tests cover our request shaping, response
parsing, retry and circuit-breaker behaviour — not DeepSeek's uptime.
"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class Prognosis(BaseModel):
    risk_level: str
    risk_probability_pct: int
    summary: str


def _chat_response(content: str, prompt_tokens: int = 120, completion_tokens: int = 40) -> dict[str, Any]:
    return {
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        },
    }


def _mock_client(status_code: int, payload: dict[str, Any] | None = None, text: str = ""):
    """Builds an httpx.AsyncClient stub usable as an async context manager."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload or {}
    response.text = text

    client = MagicMock()
    client.post = AsyncMock(return_value=response)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


@pytest.fixture
def provider():
    from app.ai.deepseek_provider import DeepSeekProvider, breaker

    breaker.record_success()  # clean slate between tests
    return DeepSeekProvider(api_key="test-key", model="deepseek-chat", max_retries=2)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def test_factory_returns_deepseek_by_default():
    from app.ai.deepseek_provider import DeepSeekProvider
    from app.ai.factory import build_ai_provider

    assert isinstance(build_ai_provider("deepseek"), DeepSeekProvider)


def test_factory_can_still_return_gemini():
    from app.ai.factory import build_ai_provider
    from app.ai.gemini_provider import GeminiProvider

    assert isinstance(build_ai_provider("gemini"), GeminiProvider)


def test_factory_rejects_unknown_provider():
    from app.ai.factory import build_ai_provider

    with pytest.raises(ValueError, match="Noma'lum AI provayder"):
        build_ai_provider("llama-on-a-toaster")


def test_clinical_service_accepts_any_provider():
    """ClinicalAIService must not be welded to one vendor."""
    from app.ai.clinical_ai import ClinicalAIService
    from app.ai.deepseek_provider import DeepSeekProvider

    service = ClinicalAIService(provider=DeepSeekProvider(api_key="x"))
    assert isinstance(service.provider, DeepSeekProvider)


# ---------------------------------------------------------------------------
# generate_text
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_text_returns_content(provider):
    client = _mock_client(200, _chat_response("Bemor holati barqaror."))

    with patch("httpx.AsyncClient", return_value=client):
        result = await provider.generate_text("Holat qanday?", system_instruction="Shifokorsan")

    assert result == "Bemor holati barqaror."


@pytest.mark.asyncio
async def test_generate_text_sends_system_then_user_message(provider):
    client = _mock_client(200, _chat_response("ok"))

    with patch("httpx.AsyncClient", return_value=client):
        await provider.generate_text("savol", system_instruction="ko'rsatma")

    payload = client.post.call_args.kwargs["json"]
    assert payload["model"] == "deepseek-chat"
    assert payload["stream"] is False
    assert [m["role"] for m in payload["messages"]] == ["system", "user"]
    assert payload["messages"][0]["content"] == "ko'rsatma"
    assert payload["messages"][1]["content"] == "savol"


@pytest.mark.asyncio
async def test_generate_text_sends_bearer_auth(provider):
    client = _mock_client(200, _chat_response("ok"))

    with patch("httpx.AsyncClient", return_value=client):
        await provider.generate_text("savol")

    headers = client.post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer test-key"


@pytest.mark.asyncio
async def test_missing_api_key_falls_back_without_calling_api():
    from app.ai.deepseek_provider import DeepSeekProvider

    keyless = DeepSeekProvider(api_key="")
    with patch("httpx.AsyncClient") as client_cls:
        result = await keyless.generate_text("savol")

    client_cls.assert_not_called()
    assert "kaliti" in result


# ---------------------------------------------------------------------------
# generate_structured
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_structured_parses_into_schema(provider):
    body = json.dumps(
        {"risk_level": "high", "risk_probability_pct": 82, "summary": "SpO2 pasaymoqda"}
    )
    client = _mock_client(200, _chat_response(body))

    with patch("httpx.AsyncClient", return_value=client):
        result = await provider.generate_structured("tahlil qil", Prognosis)

    assert isinstance(result, Prognosis)
    assert result.risk_level == "high"
    assert result.risk_probability_pct == 82


@pytest.mark.asyncio
async def test_generate_structured_requests_json_mode(provider):
    body = json.dumps({"risk_level": "low", "risk_probability_pct": 5, "summary": "ok"})
    client = _mock_client(200, _chat_response(body))

    with patch("httpx.AsyncClient", return_value=client):
        await provider.generate_structured("tahlil qil", Prognosis)

    payload = client.post.call_args.kwargs["json"]
    assert payload["response_format"] == {"type": "json_object"}
    # DeepSeek's JSON mode needs the word "json" present in the conversation.
    assert "json" in payload["messages"][0]["content"].lower()


@pytest.mark.asyncio
async def test_generate_structured_raises_on_malformed_json(provider):
    from app.core.exceptions import AIProviderException

    client = _mock_client(200, _chat_response("bu JSON emas"))

    with patch("httpx.AsyncClient", return_value=client):
        with pytest.raises(AIProviderException):
            await provider.generate_structured("tahlil qil", Prognosis)


# ---------------------------------------------------------------------------
# Retry & circuit breaker
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_retries_then_succeeds_on_transient_error(provider):
    from app.ai.deepseek_provider import DeepSeekProvider

    failing = MagicMock(status_code=503, text="overloaded")
    failing.json.return_value = {}
    ok = MagicMock(status_code=200)
    ok.json.return_value = _chat_response("qayta urinib muvaffaqiyat")
    ok.text = ""

    client = MagicMock()
    client.post = AsyncMock(side_effect=[failing, ok])
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=client), patch(
        "asyncio.sleep", new=AsyncMock()
    ):
        result = await provider.generate_text("savol")

    assert result == "qayta urinib muvaffaqiyat"
    assert client.post.await_count == 2


@pytest.mark.asyncio
async def test_non_retryable_error_raises_and_trips_failure(provider):
    from app.core.exceptions import AIProviderException

    client = _mock_client(400, {}, text="bad request")

    with patch("httpx.AsyncClient", return_value=client):
        with pytest.raises(AIProviderException):
            await provider.generate_text("savol")

    assert client.post.await_count == 1  # 400 qayta urinilmaydi


@pytest.mark.asyncio
async def test_open_breaker_fails_fast_without_network(provider):
    from app.ai.breaker import BREAKER_FAILURE_THRESHOLD, CircuitBreakerOpenError
    from app.ai.deepseek_provider import breaker

    for _ in range(BREAKER_FAILURE_THRESHOLD):
        breaker.record_failure()

    try:
        with patch("httpx.AsyncClient") as client_cls:
            with pytest.raises(CircuitBreakerOpenError):
                await provider.generate_text("savol")
        client_cls.assert_not_called()
    finally:
        breaker.record_success()


def test_breaker_reports_state_per_provider():
    from app.ai.breaker import BREAKER_FAILURE_THRESHOLD, CircuitBreaker

    a = CircuitBreaker("provider-a")
    b = CircuitBreaker("provider-b")

    for _ in range(BREAKER_FAILURE_THRESHOLD):
        a.record_failure()

    assert a.is_open is True
    assert b.is_open is False  # bir provayderning uzilishi ikkinchisini bloklamaydi
    a.record_success()


# ---------------------------------------------------------------------------
# Token accounting
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_records_real_token_usage_from_response(provider):
    from app.core.metrics import ai_tokens_total

    def _value(direction: str) -> float:
        metric = ai_tokens_total.labels(provider="deepseek", direction=direction)
        return metric._value.get()

    before_in, before_out = _value("input"), _value("output")
    client = _mock_client(200, _chat_response("javob", prompt_tokens=300, completion_tokens=90))

    with patch("httpx.AsyncClient", return_value=client):
        await provider.generate_text("savol")

    assert _value("input") - before_in == 300
    assert _value("output") - before_out == 90
