"""Image OCR summary in the ChatGPT style (description + entities + key figures).

The summary is generated with the already-configured text LLM: the OCR text
produced by ``document_extractor`` is sent to ``get_llm_provider`` with an
explicit French prompt. No new dependency, no vision model, no database or
schema change: the summary is prepended to the OCR text before chunking, so
chunk 0 of an image document always carries the summary when it exists.

A failure never blocks indexing: it is logged with a warning and the caller
falls back to the raw OCR text (never a silent ``except`` / ``pass``).
"""

from __future__ import annotations

import logging

from app.llm import get_llm_provider

_logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}

_MAX_OCR_CHARS = 4000


def summarize_image_ocr(filename: str, ocr_text: str) -> str | None:
    """Return a structured French summary of an image OCR text, or ``None``.

    The summary follows three explicit sections: description (2-3 sentences),
    entities, and key figures. ``None`` means "no summary available": empty
    input, empty model answer, or any provider failure (logged, never fatal).
    """
    cleaned = (ocr_text or "").strip()
    if not cleaned:
        return None

    system_prompt = (
        "Tu es Dexter, l'assistant pedagogique. Tu recois le texte OCR d'une image "
        "uploadee par un etudiant ou un professeur. "
        "Reponds en francais, uniquement a partir du texte fourni, sans inventer "
        "d'information. "
        "Structure ta reponse en trois sections exactes :\n"
        "Description : 2 a 3 phrases qui decrivent ce que montre l'image.\n"
        "Entites : les personnes, lieux, organisations ou notions citees "
        "(ou 'Aucune' si le texte n'en contient pas).\n"
        "Chiffres cles : les montants, dates, pourcentages ou quantites cites "
        "(ou 'Aucun' si le texte n'en contient pas)."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Image : {filename}\nTexte OCR :\n{cleaned[:_MAX_OCR_CHARS]}",
        },
    ]

    try:
        raw_response = get_llm_provider().chat(messages=messages, temperature=0.2, max_tokens=400)
    except Exception as exc:  # noqa: BLE001 - logged fallback, indexing continues with OCR alone
        _logger.warning("Image summary failed for %s: %s", filename, exc)
        return None

    summary = (raw_response or "").strip()
    if not summary:
        _logger.warning("Image summary empty for %s: indexing continues with OCR text alone.", filename)
        return None
    return summary
