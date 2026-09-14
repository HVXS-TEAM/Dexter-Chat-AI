"""OpenAI-compatible LLM provider implementation."""

from __future__ import annotations

import httpx

from app.config import settings
from app.llm.provider import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    """Provider for OpenAI-compatible APIs such as Groq, DeepSeek, and OpenAI."""

    def __init__(self) -> None:
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url.rstrip("/")
        self.model = settings.llm_model

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 512,
        model: str | None = None,
    ) -> str:
        """Send a chat completion request to the configured provider."""
        if not self.api_key:
            raise ValueError("LLM API key is not configured.")

        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices", [])
        if not choices:
            raise ValueError("LLM returned no choices.")

        message = choices[0].get("message", {})
        return str(message.get("content", ""))


_provider_singleton: OpenAICompatibleProvider | None = None


def get_llm_provider() -> LLMProvider:
    """Return the configured singleton LLM provider."""
    global _provider_singleton
    if _provider_singleton is None:
        _provider_singleton = OpenAICompatibleProvider()
    return _provider_singleton
