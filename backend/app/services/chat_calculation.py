"""Deterministic calculation branch for the chat endpoint (Approche 1).

When the classifier returns ``intention == "calcul"`` with a known domain,
this module extracts numeric parameters from the free-text question with
explicit, testable heuristics, runs the matching ``dexter-calc`` tool via
``calculator_service``, and formats the verified figures for the LLM prompt.

Rules (PRD S6/S10.5, AGENTS.md regle 6/12) :
- Never invent numbers : missing params give a clarification payload.
- Every failure is explicit (missing fields list or error message).
- Explicit readable code over compact cleverness.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any

from dexter_calc.core.registry import NoCalculatorFoundError

from app.services.calculator_service import calculator_service

logger = logging.getLogger(__name__)

_MISSING_LABELS: dict[str, dict[str, str]] = {
    "comptabilite": {
        "amount": "montant HT ou TTC",
        "rate": "taux de TVA",
    },
    "finance_van": {
        "base_amount": "investissement initial",
        "flows": "flux d'exploitation",
        "rate": "taux d'actualisation",
    },
    "finance_amortissement": {
        "amount": "valeur d'origine",
        "periods": "duree d'amortissement (periods)",
        "period_years": "annees ecoulees (period_years)",
    },
    "banque": {
        "amount": "capital",
        "rate": "taux",
        "period_months": "duree en mois",
    },
}

# Explicit currency tokens written by the student, in match-priority order.
# The label replaces the calculators' hardcoded ``unit="€"`` default (decision 1A).
_CURRENCY_LABELS: tuple[tuple[str, str], ...] = (
    (r"\bFCFA\b", "FCFA"),
    (r"\bXAF\b", "XAF"),
    (r"\bXOF\b", "XOF"),
    (r"(?:€|\bEUR(?:OS)?\b)", "€"),
    (r"(?:\$|\bUSD\b)", "$"),
)


def _parse_float(token: str) -> float | None:
    """Parse a French/English decimal token, else None."""
    cleaned = token.replace("\u00a0", "").replace(" ", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_percent_rates(question: str) -> list[float]:
    """Extract rates written with a percent sign (``20%`` -> ``0.2``)."""
    rates: list[float] = []
    for match in re.finditer(r"(\d+(?:[.,]\d+)?)\s*%", question):
        value = _parse_float(match.group(1))
        if value is None:
            continue
        rates.append(round(value / 100, 6))
    return rates


def _extract_taux_keyword_rate(question: str) -> float | None:
    """Extract a rate after the keyword ``taux`` when no percent sign."""
    match = re.search(r"taux[^0-9]{0,20}(\d+(?:[.,]\d+)?)", question.lower())
    if not match:
        return None
    value = _parse_float(match.group(1))
    if value is None:
        return None
    if value > 1:
        return round(value / 100, 6)
    return value


def _extract_amounts(question: str) -> list[float]:
    """Extract monetary amounts, excluding percents and durations."""
    masked = re.sub(r"\d+(?:[.,]\d+)?\s*%", " ", question)
    masked = re.sub(
        r"\d+(?:[.,]\d+)?\s*(?:mois|ans?|annees?)",
        " ",
        masked,
        flags=re.IGNORECASE,
    )
    amounts: list[float] = []
    for match in re.finditer(r"\d+(?:[ ]?\d{3})*(?:[.,]\d+)?", masked):
        value = _parse_float(match.group(0))
        if value is not None:
            amounts.append(value)
    return amounts


def _extract_finance_van_params(
    question_text: str,
    amounts: list[float],
    rate: float | None,
    classification: Any,
) -> tuple[dict[str, Any], list[str]]:
    """Extract VAN payload : investissement + flux + taux d'actualisation."""
    labels = _MISSING_LABELS["finance_van"]
    payload: dict[str, Any] = {
        "sous_theme": classification.sous_theme,
        "intention": "calcul",
        "reference_frame": classification.referentiel,
        "language": classification.langue,
    }
    missing: list[str] = []
    if amounts:
        payload["base_amount"] = amounts[0]
        if len(amounts) >= 2:
            payload["flows"] = amounts[1:]
        else:
            missing.append(labels["flows"])
    else:
        missing.append(labels["base_amount"])
        missing.append(labels["flows"])
    if rate is not None:
        payload["discount_rate"] = rate
    else:
        missing.append(labels["rate"])
    return payload, missing


def _extract_compta_params(
    question_text: str,
    amounts: list[float],
    rate: float | None,
    classification: Any,
) -> tuple[dict[str, Any], list[str]]:
    """Extract TVA payload : montant HT (ou TTC) + taux."""
    labels = _MISSING_LABELS["comptabilite"]
    upper = question_text.upper()
    payload: dict[str, Any] = {
        "sous_theme": classification.sous_theme,
        "intention": "calcul",
        "reference_frame": classification.referentiel,
        "language": classification.langue,
    }
    missing: list[str] = []
    if "TTC" in upper and "HT" not in upper:
        if amounts:
            payload["amount_ttc"] = amounts[0]
        else:
            missing.append(labels["amount"])
    else:
        if amounts:
            payload["amount_ht"] = amounts[0]
            if "TTC" in upper and len(amounts) >= 2:
                payload["amount_ttc"] = amounts[1]
        else:
            missing.append(labels["amount"])
    if rate is not None:
        payload["tau"] = rate
    else:
        missing.append(labels["rate"])
    return payload, missing


def extract_calculation_params(
    question: str,
    classification: Any,
) -> tuple[dict[str, Any], list[str]]:
    """Extract calculator payload and missing-field labels from free text.

    Returns ``(payload, champs_manquants)``. An empty missing list means
    the payload is complete enough to attempt the deterministic calculation.
    """
    question_text = question or ""
    domaine = classification.domaine or ""
    sous_theme = (classification.sous_theme or "").lower()

    percent_rates = _extract_percent_rates(question_text)
    if percent_rates:
        rate = percent_rates[0]
    else:
        rate = _extract_taux_keyword_rate(question_text)
    amounts = _extract_amounts(question_text)
    months, years = _extract_durations(question_text)

    if domaine == "comptabilite":
        return _extract_compta_params(question_text, amounts, rate, classification)
    if domaine == "finance" and sous_theme == "amortissement":
        labels = _MISSING_LABELS["finance_amortissement"]
        payload: dict[str, Any] = {
            "sous_theme": classification.sous_theme,
            "intention": "calcul",
            "reference_frame": classification.referentiel,
            "language": classification.langue,
        }
        missing: list[str] = []
        if amounts:
            payload["base_amount"] = amounts[0]
        else:
            missing.append(labels["amount"])
        if years:
            payload["periods"] = years[0]
            if len(years) >= 2:
                payload["period_years"] = float(years[1])
            else:
                missing.append(labels["period_years"])
        else:
            missing.append(labels["periods"])
            missing.append(labels["period_years"])
        return payload, missing
    if domaine == "finance":
        return _extract_finance_van_params(question_text, amounts, rate, classification)

    labels = _MISSING_LABELS["banque"]
    payload = {
        "sous_theme": classification.sous_theme,
        "intention": "calcul",
        "reference_frame": classification.referentiel,
        "language": classification.langue,
    }
    missing = []
    if amounts:
        payload["base_amount"] = amounts[0]
    else:
        missing.append(labels["amount"])
    if rate is not None:
        payload["tau"] = rate
    else:
        missing.append(labels["rate"])
    if months:
        payload["period_months"] = months[0]
    elif years:
        payload["period_months"] = years[0] * 12
    else:
        missing.append(labels["period_months"])
    return payload, missing


def _normalize_for_matching(text: str | None) -> str:
    """Lowercase text and strip accents so it can be compared to the registry."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _matches_vocabulary(text: str, vocabulary: str) -> bool:
    """True when the text contains the vocabulary at a word start.

    Matching at a word start (and not anywhere in the text) keeps the short
    registry id ``van`` from matching unrelated words such as ``avant``, while
    still accepting inflected forms such as ``credits``.
    """
    if not text or not vocabulary:
        return False
    return re.search(rf"\b{re.escape(vocabulary)}", text) is not None


def infer_calcul_domain(question: str, classification: Any) -> str | None:
    """Infer the calculation domain when the classifier left it empty.

    The live classifier can return ``intention == "calcul"`` with
    ``domaine=None`` (instability observed on the TVA question). Without a
    domain the deterministic branch is skipped and the question would fall
    back to free generation with unverified figures (PRD S6).

    The fallback compares the question and the classifier sub-themes to the
    vocabulary of the *calculator registry* (``tva``, ``credit``, ``van``,
    ``amortissement``): the registry is the same source of truth used to run
    the calculation, so an inferred domain is always a calculable one. A
    domain is returned only when a single domain wins; an unmatched or
    ambiguous question returns ``None`` so the caller keeps asking for a
    precision instead of guessing (regle 6/12).
    """
    question_text = _normalize_for_matching(question)
    classification_texts = [_normalize_for_matching(classification.sous_theme)]
    classification_texts.extend(
        _normalize_for_matching(item) for item in classification.question_sous_themes or []
    )

    scores: dict[str, int] = {}
    for tool in calculator_service.list_calculators():
        domain = tool.get("domain")
        vocabulary = _normalize_for_matching(tool.get("sous_theme"))
        if not domain or not vocabulary:
            continue
        score = 0
        if _matches_vocabulary(question_text, vocabulary):
            score += 1
        if any(_matches_vocabulary(text, vocabulary) for text in classification_texts):
            score += 1
        if score:
            scores[domain] = scores.get(domain, 0) + score

    if not scores:
        logger.info("Calcul domain inference: no registry vocabulary in %r", question)
        return None

    best_score = max(scores.values())
    best_domains = [domain for domain, score in scores.items() if score == best_score]
    if len(best_domains) != 1:
        logger.warning(
            "Calcul domain inference is ambiguous for %r: %s", question, scores
        )
        return None

    logger.info(
        "Calcul domain inference: %r -> %r (calculator registry vocabulary)",
        question,
        best_domains[0],
    )
    return best_domains[0]


def _extract_currency_label(question: str) -> str | None:
    """Return the currency explicitly written in the question, else None.

    The calculators declare a hardcoded default ``unit`` of ``"€"``; when the
    student writes the amounts in another currency (FCFA, USD...) the unit
    shown with the verified figure must follow the question, otherwise the
    figure and the LLM explanation disagree on the currency (regle 12).
    First matching pattern wins (``FCFA`` before the looser ``EUR`` ones).
    """
    for pattern, label in _CURRENCY_LABELS:
        if re.search(pattern, question, flags=re.IGNORECASE):
            return label
    return None


def run_deterministic_calculation(
    question: str,
    classification: Any,
) -> tuple[str, dict[str, Any] | None, list[str], str | None]:
    """Run extraction + dexter-calc, returning an explicit status tuple.

    Status is ``"ok"``, ``"missing_params"``, ``"no_calculator"`` or
    ``"calc_error"``. Tuple is ``(status, calcul_result, missing, error)``
    so the router can answer without ever hiding a failure (regle 6).
    """
    payload, missing = extract_calculation_params(question, classification)
    if missing:
        return "missing_params", None, missing, None

    # The question's explicit currency is forwarded to dexter-calc (decision 1A
    # root fix) so the calculators format their unit AND pedagogical notes with
    # it, then re-applied below as a safety net for any calculator that ignores
    # display_currency (regle 7: the fallback is labelled, not hidden).
    currency_label = _extract_currency_label(question)
    if currency_label is not None:
        payload["display_currency"] = currency_label

    domaine = classification.domaine or ""
    try:
        calcul_result = calculator_service.calculate(domaine, payload)
    except NoCalculatorFoundError as exc:
        # The chat sous_theme comes from free-text LLM classification and can
        # use the domain-catalogue vocabulary (e.g. "analyse de credit") instead
        # of the registry one (e.g. "credit"). Retry with a domain-only
        # resolution ONLY when that domain has exactly one registered tool, so
        # an ambiguous domain (e.g. finance: VAN vs amortissement) keeps failing
        # explicitly instead of picking an arbitrary calculator (regle 6).
        domain_tools = [
            tool
            for tool in calculator_service.list_calculators()
            if tool.get("domain") == domaine
        ]
        if len(domain_tools) != 1:
            logger.warning("No calculator for chat calcul branch: %s", exc)
            return "no_calculator", None, [], str(exc)
        logger.warning(
            "Chat calcul: sous_theme %r is not registered for %s; "
            "using the only registered tool instead.",
            payload.get("sous_theme"),
            domaine,
        )
        try:
            calcul_result = calculator_service.calculate(
                domaine, {**payload, "sous_theme": None}
            )
        except NoCalculatorFoundError as fallback_exc:
            return "no_calculator", None, [], str(fallback_exc)
    except Exception as exc:
        logger.warning("Deterministic calculation failed: %s", exc)
        return "calc_error", None, [], str(exc)
    # Safety net (decision 1A): force the unit AND strip any leftover hardcoded
    # "€" from the pedagogical note so the figures, the prompt block and the UI
    # panel all show the currency the student actually wrote, even when a
    # calculator does not honour display_currency.
    if currency_label is not None:
        calcul_result["unit"] = currency_label
        note = calcul_result.get("pedagogical_note")
        if isinstance(note, str) and "€" in note:
            calcul_result["pedagogical_note"] = note.replace("€", currency_label)
    return "ok", calcul_result, [], None


def build_calculation_context(calcul_result: dict[str, Any]) -> str:
    """Format verified figures as a prompt block for the LLM."""
    extra = calcul_result.get("extra") or {}
    detail_lines = [f"- {key} = {value}" for key, value in extra.items()]
    if detail_lines:
        details = "\n".join(detail_lines)
    else:
        details = "- (aucun detail)"
    unit = calcul_result.get("unit") or ""
    header = (
        "[Resultat de calcul verifie (dexter-calc) — a utiliser EXCLUSIVEMENT, "
        "sans jamais le recalculer ni l'arrondir differemment]\n"
        f"- Outil : {calcul_result.get('label')} "
        f"({calcul_result.get('domain')}/{calcul_result.get('sous_theme')})\n"
        f"- Resultat principal : {calcul_result.get('result')} {unit}"
    )
    note = f"- Note pedagogique du calculateur : {calcul_result.get('pedagogical_note')}"
    return f"{header}\n{details}\n{note}"


def _extract_durations(question: str) -> tuple[list[int], list[int]]:
    """Return (durations in months, durations in years) found in the text."""
    lowered = question.lower()
    months = [int(m.group(1)) for m in re.finditer(r"(\d+)\s*mois", lowered)]
    years = [int(m.group(1)) for m in re.finditer(r"(\d+)\s*(?:ans?|ann[eé]es?)", lowered)]
    return months, years
