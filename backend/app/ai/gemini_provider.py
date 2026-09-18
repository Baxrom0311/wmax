from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Type, TypeVar

import httpx
from pydantic import BaseModel

from app.ai.provider import AIProvider
from app.core.config import settings
from app.core.exceptions import AIProviderException

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(AIProvider):
    """Production Google Gemini client with retry, structured JSON, and streaming."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 20.0,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
        self.timeout = timeout
        self.max_retries = max_retries

    def count_tokens(self, text: str) -> int:
        """Approximates token count (4 chars ~ 1 token for English, 2 chars for Uzbek/Cyrillic)."""
        return max(1, len(text) // 3)

    def _build_safety_settings(self) -> list[dict[str, str]]:
        """Medical systems require relaxed harassment/hate filters so physiological terms aren't blocked."""
        return [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_ONLY_HIGH",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH",
            },
        ]

    async def _execute_with_retry(
        self, endpoint: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Executes Gemini API POST with exponential backoff on transient errors."""
        url = f"{GEMINI_API_BASE}/{self.model}:{endpoint}?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        delay = 1.0
        last_err: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, headers=headers, json=payload)

                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code in [429, 500, 502, 503, 504]:
                        logger.warning(
                            f"Gemini API returned {response.status_code}, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                        )
                        await asyncio.sleep(delay)
                        delay *= 2.0
                        continue
                    else:
                        error_detail = response.text
                        logger.error(f"Gemini API error ({response.status_code}): {error_detail}")
                        raise AIProviderException(
                            f"Gemini xizmati xatolik qaytardi: {response.status_code}",
                            details={"api_response": error_detail},
                        )
            except (httpx.TimeoutException, httpx.NetworkError) as err:
                last_err = err
                logger.warning(
                    f"Network error communicating with Gemini ({err}), retrying in {delay}s"
                )
                await asyncio.sleep(delay)
                delay *= 2.0

        raise AIProviderException(
            f"Gemini xizmati bilan aloqa o'rnatib bo'lmadi: {last_err}"
        )

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        if not self.api_key:
            logger.info("GEMINI_API_KEY is not configured; returning fallback heuristic")
            return "Gemini API kaliti ko'rsatilmagan. Standart klinik qoidalar asosida monitoring faol."

        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
            "safetySettings": self._build_safety_settings(),
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        data = await self._execute_with_retry("generateContent", payload)
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                return "Javob generatsiya qilinmadi."
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts)
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return "Klinik xulosa tayyorlashda xatolik yuz berdi."

    async def generate_structured(
        self,
        prompt: str,
        schema_class: Type[T],
        system_instruction: str | None = None,
        temperature: float = 0.1,
    ) -> T:
        """Generates JSON from Gemini and strictly validates it with schema_class."""
        if not self.api_key:
            # Safe default fallback for offline / mock testing
            raise AIProviderException("GEMINI_API_KEY o'rnatilmagan")

        json_schema = schema_class.model_json_schema()
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
            "safetySettings": self._build_safety_settings(),
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        data = await self._execute_with_retry("generateContent", payload)
        try:
            candidates = data.get("candidates", [])
            text_json = candidates[0]["content"]["parts"][0]["text"]
            parsed_dict = json.loads(text_json)
            return schema_class.model_validate(parsed_dict)
        except Exception as err:
            logger.error(f"Structured output parsing failed: {err}")
            raise AIProviderException(
                f"Gemini tuzilgan JSON javobini o'qib bo'lmadi: {err}"
            ) from err

    async def stream_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        """Streams text chunks using Gemini streamGenerateContent SSE."""
        if not self.api_key:
            yield "Gemini API kaliti yo'q."
            return

        url = f"{GEMINI_API_BASE}/{self.model}:streamGenerateContent?key={self.api_key}"
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                async for chunk in response.aiter_text():
                    if chunk:
                        yield chunk
