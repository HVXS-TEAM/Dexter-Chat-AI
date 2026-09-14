"""Quiz request and response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuizGenerateRequest(BaseModel):
    """Input for quiz generation."""

    domaine: str = Field(..., min_length=1)
    sous_theme: str | None = None
    referentiel: str | None = None


class QuizGenerateResponse(BaseModel):
    """Quiz returned without the correction until submission."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    domaine: str
    sous_theme: str | None
    referentiel: str | None
    enonce: str
    statut: str
    created_at: datetime


class QuizSubmitRequest(BaseModel):
    """Student answer for correction."""

    reponse_etudiant: str = Field(..., min_length=1)

    @field_validator("reponse_etudiant")
    @classmethod
    def validate_answer(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Answer cannot be empty.")
        return cleaned


class QuizSubmitResponse(BaseModel):
    """Correction with score and feedback."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    domaine: str
    sous_theme: str | None
    referentiel: str | None
    enonce: str
    reponse_etudiant: str
    corrige: str | None = None
    score: float | None
    feedback_corrige: str | None
    statut: str


class QuizProgressItem(BaseModel):
    """One quiz attempt in the progress history."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    domaine: str
    sous_theme: str | None
    referentiel: str | None
    statut: str
    score: float | None
    created_at: datetime


class QuizProgressResponse(BaseModel):
    """History and aggregate information for a user."""

    model_config = ConfigDict(from_attributes=True)

    attempts: list[QuizProgressItem]
    total_attempts: int
    submitted_attempts: int
    average_score: float | None
    by_domain: dict[str, int]


class QuizDetailResponse(BaseModel):
    """Single attempt re-read by its owner, correction masked until submit."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    domaine: str
    sous_theme: str | None
    referentiel: str | None
    enonce: str
    reponse_etudiant: str | None = None
    corrige: str | None = None
    score: float | None = None
    feedback_corrige: str | None = None
    statut: str
    created_at: datetime
