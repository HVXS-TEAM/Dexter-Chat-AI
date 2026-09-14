"""Abstract LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator


class LLMProvider(ABC):
    """Common interface for all LLM providers."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 512,
        model: str | None = None,
    ) -> str:
        """Send a chat completion request and return the raw text response."""
        raise NotImplementedError

    def stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 512,
        model: str | None = None,
    ) -> Iterator[str]:
        """Yield text fragments from a streaming chat completion."""
        raise NotImplementedError("This LLM provider does not support streaming.")
