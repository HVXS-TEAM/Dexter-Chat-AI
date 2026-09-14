"""Document text chunking utilities."""

from __future__ import annotations

import re


def chunk_text(text: str, max_chars: int = 800, overlap: int = 100) -> list[tuple[str, int]]:
    """Split text into paragraph-aware chunks with bounded overlap."""
    if max_chars <= 0 or overlap < 0 or overlap >= max_chars:
        raise ValueError("max_chars must be positive and overlap must be smaller than max_chars.")

    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    chunks: list[tuple[str, int]] = []
    current = ""

    def append_chunk(value: str) -> None:
        if value.strip():
            chunks.append((value.strip(), len(chunks)))

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                append_chunk(current)
                current = ""
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            fragment = ""
            for sentence in sentences:
                if len(fragment) + len(sentence) + 1 <= max_chars:
                    fragment = f"{fragment} {sentence}".strip()
                else:
                    append_chunk(fragment)
                    fragment = sentence
            if fragment:
                append_chunk(fragment)
            continue

        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
        else:
            append_chunk(current)
            prefix = current[-overlap:] if overlap else ""
            current = f"{prefix}\n\n{paragraph}".strip()
            if len(current) > max_chars:
                append_chunk(current[:max_chars])
                current = current[max_chars - overlap :] if overlap else ""

    if current:
        append_chunk(current)
    return chunks
