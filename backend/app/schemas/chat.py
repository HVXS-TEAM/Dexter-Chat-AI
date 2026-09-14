"""Chat classification and conversation schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ClassifyRequest(BaseModel):
    """Input for the generic domain classifier."""

    question: str = Field(..., min_length=1)
    historique: str | None = None

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty.")
        return cleaned


class ClassificationResult(BaseModel):
    """Structured output of the domain classifier."""

    domaine: str | None = None
    sous_theme: str | None = None
    referentiel: str | None = None
    intention: Literal[
        "explication",
        "calcul",
        "cas_pratique",
        "generation_exercice",
        "correction",
        "autre",
    ] = "autre"
    langue: Literal["fr", "en"] = "fr"
    confiance: float = Field(default=0.0, ge=0.0, le=1.0)
    besoin_precision: bool = False
    question_sous_themes: list[str] = Field(default_factory=list)


class ChatMessageRequest(BaseModel):
    """Input for the authenticated conversational endpoint."""

    question: str = Field(..., min_length=1)
    historique: str | None = None
    conversation_id: int | None = None

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty.")
        return cleaned


class ChatMessageResponse(BaseModel):
    """Response from the two-stage conversational flow."""

    reponse: str | None = None
    mode: Literal["explique_moi", "mes_cours", "calcul"] = "explique_moi"
    domaine: str | None = None
    sous_theme: str | None = None
    referentiel: str | None = None
    clarification_demandee: bool
    question_sous_themes: list[str] = Field(default_factory=list)
    referentiels_proposes: list[str] | None = None
    conversation_id: int | None = None
    calcul_result: dict | None = None
    champs_manquants: list[str] = Field(default_factory=list)
