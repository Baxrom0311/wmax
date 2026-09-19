from __future__ import annotations

import logging

from app.ai.provider import AIProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = ("deepseek", "gemini")


def build_ai_provider(name: str | None = None) -> AIProvider:
    """Returns the configured LLM client.

    Providers are imported lazily so a deployment that uses only one of them
    never pays for the other's module import — and a broken optional provider
    cannot stop the API from starting.
    """
    provider_name = (name or settings.AI_PROVIDER).strip().lower()

    if provider_name == "deepseek":
        from app.ai.deepseek_provider import DeepSeekProvider

        return DeepSeekProvider()

    if provider_name == "gemini":
        from app.ai.gemini_provider import GeminiProvider

        return GeminiProvider()

    raise ValueError(
        f"Noma'lum AI provayder: {provider_name!r}. "
        f"Mavjud variantlar: {', '.join(SUPPORTED_PROVIDERS)}"
    )
