from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.auth import UserResponse
from app.auth.dependencies import get_current_user
from app.services.calculator_service import calculator_service

router = APIRouter()

# Calculator-related chat response schema
from pydantic import BaseModel
from typing import Any


class ChatRequest(BaseModel):
    question: str
    history: list[dict[str, Any]] | None = None


class ChatResponse(BaseModel):
    question: str
    domain: str | None = None
    sous_theme: str | None = None
    intention: str | None = None
    clarification_demandee: bool = False
    reponse: str | None = None
    calcul_result: dict[str, Any] | None = None
    mode: str = "chat"


@router.post("/chat/message", response_model=ChatResponse)
def chat_message(
    payload: ChatRequest,
    user=Depends(get_current_user),
):
    """Route de chat avec detection d'intention de calcul.

    Si la question est une intention de calcul reconnue (via le LLM classifier),
    le systeme route automatiquement vers le calculateur approprie et renvoie
    le resultat pedagogique.
    """
    question = payload.question

    # Simple keyword-based intent detection (placeholder for LLM classifier)
    # In production, this calls the LLM classifier service
    intention, domain = _detect_intention(question)

    if intention == "calcul" and domain:
        try:
            calcul_input = _build_calculator_input(question, domain)
            result = calculator_service.calculate(domain, calcul_input)
            return ChatResponse(
                question=question,
                domain=domain,
                sous_theme=result.get("sous_theme"),
                intention="calcul",
                clarification_demandee=False,
                reponse=result.get("pedagogical_note"),
                calcul_result=result,
                mode="calcul",
            )
        except Exception as exc:
            return ChatResponse(
                question=question,
                domain=domain,
                intention="calcul",
                clarification_demandee=True,
                reponse=f"Impossible de calculer: {str(exc)}. Precisez votre question.",
                mode="chat",
            )

    # Fallback: no calculation intent detected
    return ChatResponse(
        question=question,
        intention="chat",
        reponse="Posez-moi une question sur la comptabilite, la finance ou la banque.",
        mode="chat",
    )


def _detect_intention(question: str) -> tuple[str, str | None]:
    """Keyword-based detection of calculation intent and domain."""
    q = question.lower()

    # Comptabilite / TVA
    if any(k in q for k in ["tva", "ht", "ttc", "taxe", "facture"]):
        return "calcul", "comptabilite"

    # Finance / VAN / Amortissement
    if any(k in q for k in ["van", "actualisation", "rentabilite", "investissement", "amortissement", "dotation"]):
        return "calcul", "finance"

    # Banque / Credit
    if any(k in q for k in ["credit", "interet", "taux", "mensualite", "emprunt", "placement"]):
        return "calcul", "banque"

    return "chat", None


def _build_calculator_input(question: str, domain: str) -> dict[str, Any]:
    """Extract numeric values from question for calculator input."""
    import re

    payload: dict[str, Any] = {}

    # Extract amounts (numbers with optional decimal)
    numbers = re.findall(r"(\d+(?:[.,]\d+)?)", question.replace(" ", ""))
    amounts = [float(n.replace(",", ".")) for n in numbers]

    # Extract percentage rates
    rates = re.findall(r"(\d+(?:[.,]\d+)?)\s*%", question)
    rate_values = [float(r.replace(",", ".")) / 100 for r in rates]

    if domain == "comptabilite":
        if amounts:
            payload["amount_ht"] = amounts[0]
        if rate_values:
            payload["tau"] = rate_values[0]
        elif any(k in question.lower() for k in ["tva"]):
            payload["tau"] = 0.2  # Default French VAT rate

    elif domain == "finance":
        if amounts:
            payload["base_amount"] = amounts[0]
            if len(amounts) > 1:
                payload["flows"] = amounts[1:]
        if rate_values:
            payload["discount_rate"] = rate_values[0]

    elif domain == "banque":
        if amounts:
            payload["base_amount"] = amounts[0]
        if rate_values:
            payload["tau"] = rate_values[0]
        # Default duration
        if "mois" in question.lower():
            months = re.findall(r"(\d+)\s*mois", question.lower())
            if months:
                payload["period_months"] = int(months[0])
            else:
                payload["period_months"] = 12

    return payload
