"""Lazy multilingual embedding service."""

from __future__ import annotations

from typing import Any

from app.config import settings

_model_cache: Any = None


def get_embedding_model() -> Any:
    """Load and cache the configured embedding model lazily."""
    global _model_cache
    if _model_cache is None:
        from sentence_transformers import SentenceTransformer

        _model_cache = SentenceTransformer(settings.embedding_model)
    return _model_cache


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts into normalized 384-dimensional vectors."""
    if not texts:
        return []
    embeddings = get_embedding_model().encode(texts, normalize_embeddings=True)
    return [embedding.tolist() for embedding in embeddings]


def embed_text(text: str) -> list[float]:
    """Embed one text."""
    return embed_texts([text])[0]
