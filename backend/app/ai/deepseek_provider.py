from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator, Type, TypeVar

import httpx
from pydantic import BaseModel

from app.ai.breaker import CircuitBreaker
from app.ai.provider import AIProvider
from app.core.config import settings
from app.core.exceptions import AIProviderException
from app.core.metrics import ai_request_duration_seconds, ai_tokens_total

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

PROVIDER_NAME = "deepseek"

# DeepSeek speaks the OpenAI chat-completions dialect, so the payload shape here
# also works against any OpenAI-compatible gateway by changing the base URL.
CHAT_COMPLETIONS_PATH = "/chat/completions"

RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})

breaker = CircuitBreaker(PROVIDER_NAME)


class DeepSeekProvider(AIProvider):
    """DeepSeek chat-completions client with retry, JSON mode, and streaming.

    Unlike the Gemini client this reports **real** token usage: the API returns
    `usage.prompt_tokens` / `usage.completion_tokens`, so the token metrics stop
    being an estimate. `count_tokens` remains an approximation for the
    pre-flight budget check only.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.DEEPSEEK_API_KEY
        self.model = model or settings.DEEPSEEK_MODEL
        self.base_url = (base_url or settings.DEEPSEEK_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    # ── helpers ──────────────────────────────────────────────────────────────

    def count_tokens(self, text: str) -> int:
        """Approximates token count (~3 chars per token for Uzbek/Cyrillic mixes)."""
        return max(1, len(text) // 3)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _messages(prompt: str, system_instruction: str | None) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        return messages

    @staticmethod
    def _record_usage(data: dict[str, Any]) -> None:
        """Records the provider's own token accounting when present."""
        usage = data.get("usage") or {}
        if prompt_tokens := usage.get("prompt_tokens"):
            ai_tokens_total.labels(provider=PROVIDER_NAME, direction="input").inc(
                prompt_tokens
            )
        if completion_tokens := usage.get("completion_tokens"):
            ai_tokens_total.labels(provider=PROVIDER_NAME, direction="output").inc(
                completion_tokens
            )

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            return ""
        return (choices[0].get("message") or {}).get("content") or ""

    # ── transport ────────────────────────────────────────────────────────────

    async def _execute_with_retry(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POSTs to DeepSeek with exponential backoff on transient errors."""
        breaker.raise_if_open()

        url = f"{self.base_url}{CHAT_COMPLETIONS_PATH}"
        delay = 1.0
        last_err: Exception | None = None
        started = time.perf_counter()

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url, headers=self._headers(), json=payload
                    )

                    if response.status_code == 200:
                        ai_request_duration_seconds.labels(
                            provider=PROVIDER_NAME
                        ).observe(time.perf_counter() - started)
                        breaker.record_success()
                        data = response.json()
                        self._record_usage(data)
                        return data

                    if response.status_code in RETRYABLE_STATUS:
                        logger.warning(
                            "DeepSeek returned %s, retrying in %.1fs (attempt %d/%d)",
                            response.status_code,
                            delay,
                            attempt + 1,
                            self.max_retries,
                        )
                        await asyncio.sleep(delay)
                        delay *= 2.0
                        continue

                    detail = response.text
                    logger.error(
                        "DeepSeek API error (%s): %s", response.status_code, detail
                    )
                    ai_request_duration_seconds.labels(provider=PROVIDER_NAME).observe(
                        time.perf_counter() - started
                    )
                    breaker.record_failure()
                    raise AIProviderException(
                        f"DeepSeek xizmati xatolik qaytardi: {response.status_code}",
                        details={"api_response": detail},
                    )
            except (httpx.TimeoutException, httpx.NetworkError) as err:
                last_err = err
                logger.warning(
                    "Network error communicating with DeepSeek (%s), retrying in %.1fs",
                    err,
                    delay,
                )
                await asyncio.sleep(delay)
                delay *= 2.0

        ai_request_duration_seconds.labels(provider=PROVIDER_NAME).observe(
            time.perf_counter() - started
        )
        breaker.record_failure()
        raise AIProviderException(
            f"DeepSeek xizmati bilan aloqa o'rnatib bo'lmadi: {last_err}"
        )

    # ── AIProvider interface ─────────────────────────────────────────────────

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        if not self.api_key:
            logger.info("DEEPSEEK_API_KEY is not configured; returning fallback text")
            return (
                "DeepSeek API kaliti ko'rsatilmagan. "
                "Standart klinik qoidalar asosida monitoring faol."
            )

        data = await self._execute_with_retry(
            {
                "model": self.model,
                "messages": self._messages(prompt, system_instruction),
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
            }
        )

        text = self._extract_text(data)
        return text.strip() if text else "Javob generatsiya qilinmadi."

    async def generate_structured(
        self,
        prompt: str,
        schema_class: Type[T],
        system_instruction: str | None = None,
        temperature: float = 0.1,
    ) -> T:
        if not self.api_key:
            raise AIProviderException("DEEPSEEK_API_KEY o'rnatilmagan")

        # DeepSeek's JSON mode requires the word "json" to appear in the
        # conversation, and it does not accept a JSON schema the way Gemini
        # does — so the shape is described in the system message instead.
        schema_hint = json.dumps(
            schema_class.model_json_schema(), ensure_ascii=False, indent=2
        )
        system = (
            f"{system_instruction}\n\n" if system_instruction else ""
        ) + (
            "Javobni FAQAT quyidagi JSON schema'ga mos JSON obyekt sifatida qaytar. "
            "Hech qanday izoh, markdown yoki kod bloki qo'shma.\n\n"
            f"JSON schema:\n{schema_hint}"
        )

        data = await self._execute_with_retry(
            {
                "model": self.model,
                "messages": self._messages(prompt, system),
                "temperature": temperature,
                "response_format": {"type": "json_object"},
                "stream": False,
            }
        )

        raw = self._extract_text(data)
        try:
            return schema_class.model_validate(json.loads(raw))
        except Exception as err:
            logger.error("Structured output parsing failed: %s — raw: %.300s", err, raw)
            raise AIProviderException(
                f"DeepSeek tuzilgan JSON javobini o'qib bo'lmadi: {err}"
            ) from err

    async def stream_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            yield "DeepSeek API kaliti yo'q."
            return

        breaker.raise_if_open()

        url = f"{self.base_url}{CHAT_COMPLETIONS_PATH}"
        payload = {
            "model": self.model,
            "messages": self._messages(prompt, system_instruction),
            "temperature": temperature,
            "stream": True,
        }

        started = time.perf_counter()
        collected: list[str] = []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", url, headers=self._headers(), json=payload
                ) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        breaker.record_failure()
                        raise AIProviderException(
                            f"DeepSeek oqim xatoligi: {response.status_code}",
                            details={"api_response": body.decode("utf-8", "replace")},
                        )

                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        chunk = line[len("data:"):].strip()
                        if chunk == "[DONE]":
                            break
                        try:
                            delta = (
                                json.loads(chunk)["choices"][0]
                                .get("delta", {})
                                .get("content")
                            )
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
                        if delta:
                            collected.append(delta)
                            yield delta

            breaker.record_success()
        finally:
            # Streaming responses carry no usage block, so fall back to the
            # local estimate — counted once, not per chunk.
            ai_request_duration_seconds.labels(provider=PROVIDER_NAME).observe(
                time.perf_counter() - started
            )
            prompt_tokens = self.count_tokens(prompt)
            if system_instruction:
                prompt_tokens += self.count_tokens(system_instruction)
            ai_tokens_total.labels(provider=PROVIDER_NAME, direction="input").inc(
                prompt_tokens
            )
            if collected:
                ai_tokens_total.labels(provider=PROVIDER_NAME, direction="output").inc(
                    self.count_tokens("".join(collected))
                )
