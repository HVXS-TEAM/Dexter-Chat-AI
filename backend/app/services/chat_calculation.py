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

    domaine = classification.domaine or ""
    try:
        calcul_result = calculator_service.calculate(domaine, payload)
    except NoCalculatorFoundError as exc:
        logger.warning("No calculator for chat calcul branch: %s", exc)
        return "no_calculator", None, [], str(exc)
    except Exception as exc:
        logger.warning("Deterministic calculation failed: %s", exc)
        return "calc_error", None, [], str(exc)
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
