"""Generic domain classification service."""

from __future__ import annotations

import json
import logging
import re

from app.domains.loader import domain_prompt_context, get_domain, list_domains
from app.llm import get_llm_provider
from app.schemas.chat import ClassificationResult

_logger = logging.getLogger(__name__)


def _extract_json_block(text: str) -> str | None:
    """Extract a JSON object from a model response, even with extra text."""
    if not text:
        return None

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)

    return None


def _fallback_result(question: str) -> ClassificationResult:
    """Return a safe low-confidence result when classification fails."""
    domains = list_domains()
    best_match = None
    best_score = 0

    for domain in domains:
        score = 0
        text = (question or "").lower()
        for keyword in domain.get("keywords", []):
            if keyword.lower() in text:
                score += 1
        if score > best_score:
            best_score = score
            best_match = domain

    question_subthemes = []
    if best_match is not None:
        question_subthemes = [
            item for item in best_match.get("sous_themes", []) if item.lower() in (question or "").lower()
        ]
        if not question_subthemes:
            question_subthemes = best_match.get("sous_themes", [])[:2]

    return ClassificationResult(
        domaine=None,
        sous_theme=None,
        referentiel=None,
        intention="autre",
        langue="fr" if any(ch in (question or "").lower() for ch in ["bonjour", "merci", "explique", "calcule", "bilan", "finance"]) else "en",
        confiance=0.0,
        besoin_precision=True,
        question_sous_themes=question_subthemes,
    )


def classify(question: str, history_context: str | None = None) -> ClassificationResult:
    """Classify a question by domain, sub-theme, intent, and language."""
    domains = list_domains()
    if not domains:
        return ClassificationResult(confiance=0.0, besoin_precision=True, question_sous_themes=[])

    provider = get_llm_provider()
    system_prompt = (
        "You are a domain-classification router for Dexter. "
        "Return strict JSON only with no markdown fences. "
        "Use a domain id from the configured domain set only. "
        "If the question is outside the configured domains, set domaine to null. "
        "Set besoin_precision to true whenever details are missing or confidence is low.\n\n"
        f"Configured domains:\n{domain_prompt_context()}\n\n"
        "Rules:\n"
        "- Output JSON with keys: domaine, sous_theme, referentiel, intention, langue, confiance, besoin_precision, question_sous_themes.\n"
        "- intention must be one of: explication, calcul, cas_pratique, generation_exercice, correction, autre.\n"
        "- langue must be 'fr' or 'en'.\n"
        "- confiance is a float between 0 and 1.\n"
        "- If confidence < 0.6 or besoin_precision is true, set domaine to null and fill question_sous_themes with the most relevant domain subthemes from the closest configured domain.\n"
        "- If referentiel is relevant for the domain but absent, set besoin_precision to true.\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Question: {question}\nHistory: {history_context or 'None'}"},
    ]

    try:
        raw_response = provider.chat(messages=messages, temperature=0.1, max_tokens=512)
    except Exception as exc:
        # Graceful degradation: classification must never crash the endpoint.
        # The warning keeps the failure visible (no API key or full response logged).
        _logger.warning("LLM classification failed: %s", exc)
        return _fallback_result(question)

    json_text = _extract_json_block(raw_response)
    if not json_text:
        _logger.warning("LLM classification returned no JSON block.")
        return _fallback_result(question)

    try:
        payload = json.loads(json_text)
        if not isinstance(payload, dict):
            raise ValueError("Classification payload is not an object.")
        result = ClassificationResult.model_validate(payload)
    except (json.JSONDecodeError, ValueError, TypeError):
        _logger.warning("LLM classification response could not be parsed.")
        return _fallback_result(question)

    if result.confiance < 0.6:
        # Low confidence: discard the domain and propose sub-themes from the
        # closest configured domain so the user can disambiguate (PRD §5.4).
        matches = []
        target_text = (question or "").lower()
        for domain in domains:
            score = 0
            for keyword in domain.get("keywords", []):
                if keyword.lower() in target_text:
                    score += 1
            if score > 0:
                matches.append((score, domain))
        if matches:
            best_domain = max(matches, key=lambda item: item[0])[1]
            result.domaine = None
            result.question_sous_themes = best_domain.get("sous_themes", [])[:3]
        else:
            result.domaine = None
            result.question_sous_themes = []
        result.besoin_precision = True

    # High confidence with a missing detail (e.g. referential, PRD §2.1):
    # the domain is KEPT, besoin_precision stays true to ask for the detail,
    # and sub-themes are proposed from the kept domain.
    if result.domaine is not None:
        domain = get_domain(result.domaine)
        if domain is not None and result.question_sous_themes == []:
            result.question_sous_themes = domain.get("sous_themes", [])[:3]

    if result.langue not in {"fr", "en"}:
        result.langue = "fr"

    return result
