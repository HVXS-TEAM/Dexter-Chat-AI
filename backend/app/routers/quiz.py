"""Quiz endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.quiz import (
    QuizDetailResponse,
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizProgressItem,
    QuizProgressResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from app.services.quiz_service import (
    QuizGenerationError,
    UnknownDomainError,
    generate_quiz,
    get_attempt,
    list_attempts,
    submit_quiz,
)

router = APIRouter(tags=["quiz"])


@router.post("/quiz/generate", response_model=QuizGenerateResponse, status_code=status.HTTP_201_CREATED)
def generate_quiz_endpoint(
    payload: QuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizGenerateResponse:
    """Generate an exercise for the authenticated user."""
    try:
        return generate_quiz(db, current_user, payload.domaine, payload.sous_theme, payload.referentiel)
    except UnknownDomainError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except QuizGenerationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Quiz generation failed.") from exc


@router.post("/quiz/{attempt_id}/submit", response_model=QuizSubmitResponse)
def submit_quiz_endpoint(
    attempt_id: int,
    payload: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizSubmitResponse:
    """Submit an answer and reveal the correction and score."""
    attempt = get_attempt(db, attempt_id, current_user.id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found.")

    if attempt.statut == "corrige":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz attempt already submitted.")

    try:
        return submit_quiz(db, attempt, current_user, payload.reponse_etudiant)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/quiz/{attempt_id}", response_model=QuizDetailResponse)
def read_quiz_attempt(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizDetailResponse:
    """Re-read one owned attempt, masking the correction until submit."""
    attempt = get_attempt(db, attempt_id, current_user.id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found.")

    if attempt.statut == "corrige":
        return attempt
    masked = QuizDetailResponse.model_validate(attempt)
    masked.corrige = None
    masked.feedback_corrige = None
    masked.score = None
    return masked


@router.get("/users/me/progress", response_model=QuizProgressResponse)
def read_user_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizProgressResponse:
    """Return the user's recent quiz attempts and simple progress aggregates."""
    attempts = list_attempts(db, current_user.id)
    scores = [attempt.score for attempt in attempts if attempt.score is not None]
    by_domain: dict[str, int] = {}
    for attempt in attempts:
        by_domain[attempt.domaine] = by_domain.get(attempt.domaine, 0) + 1

    progress_items = [
        QuizProgressItem(
            id=attempt.id,
            domaine=attempt.domaine,
            sous_theme=attempt.sous_theme,
            referentiel=attempt.referentiel,
            statut=attempt.statut,
            score=attempt.score,
            created_at=attempt.created_at,
        )
        for attempt in attempts
    ]

    average_score = round(sum(scores) / len(scores), 2) if scores else None
    return QuizProgressResponse(
        attempts=progress_items,
        total_attempts=len(attempts),
        submitted_attempts=sum(1 for attempt in attempts if attempt.statut == "corrige"),
        average_score=average_score,
        by_domain=by_domain,
    )
