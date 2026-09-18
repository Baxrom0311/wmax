from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class AIProvider(ABC):
    """Abstract LLM Provider interface allowing hot-swapping between Gemini, OpenAI, Claude."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        """Generates unstructured text response."""
        ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema_class: Type[T],
        system_instruction: str | None = None,
        temperature: float = 0.1,
    ) -> T:
        """Generates structured response parsed strictly into a Pydantic model."""
        ...

    @abstractmethod
    async def stream_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        """Streams token response asynchronously."""
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Approximates token count for budget management."""
        ...
