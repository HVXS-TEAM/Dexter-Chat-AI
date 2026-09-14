"""Quiz generation, correction, and progress service."""

from __future__ import annotations

import logging
import re
from string import Template

from sqlalchemy.orm import Session

from app.config import settings
from app.domains.loader import get_domain
from app.llm import get_llm_provider
from app.models.quiz import QuizAttempt
from app.models.user import User
from app.prompts.loader import build_domain_prompt


logger = logging.getLogger(__name__)


class UnknownDomainError(ValueError):
    """Raised when the requested domain is not configured."""

    pass


class QuizGenerationError(RuntimeError):
    """Raised when the LLM fails to generate a quiz exercise."""

    pass


def _tokenize(value: str) -> set[str]:
    """Return normalized tokens with a minimal length threshold."""
    words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:['-][A-Za-zÀ-ÖØ-öø-ÿ]+)?", value.lower())
    return {word for word in words if len(word) >= 4}


def _score_answer(corrige: str | None, reponse: str) -> float | None:
    """Compute a deterministic keyword-overlap score between the model answer and the student answer."""
    if corrige is None:
        return None

    corrige_tokens = _tokenize(corrige)
    reponse_tokens = _tokenize(reponse)
    if not corrige_tokens:
        return 0.0

    overlap = len(corrige_tokens & reponse_tokens)
    score = (overlap / len(corrige_tokens)) * 100
    return round(float(min(max(score, 0.0), 100.0)), 2)


_CORRIGE_MARKER = re.compile(
    r"(?:#{1,3}\s*CORRIG[ÉE].*|CORRIG[ÉE]\s*:)",
    re.IGNORECASE | re.MULTILINE,
)
_ENONCE_PREFIX = re.compile(
    r"^\s*(?:#{1,3}\s*)?(?:ÉNONC[ÉE]|ENONCE|EXERCICE)\s*:?",
    re.IGNORECASE,
)


def _split_quiz_response(response: str) -> tuple[str, str | None]:
    """Separate the exercise statement from the model correction.

    Tolerant to marker variants (``CORRIGE:``, ``Corrigé:``,
    ``### CORRIGÉ`` with or without a colon) so a slightly off-format
    model answer still yields a usable correction instead of silently
    dropping it. A heading-style marker requires the ``#`` prefix or a
    colon to avoid splitting plain prose starting with "corrige".
    """
    normalized = response.strip()
    if not normalized:
        return "", None

    match = _CORRIGE_MARKER.search(normalized)
    if match is None:
        return normalized, None

    enonce = normalized[: match.start()].strip()
    corrige = normalized[match.end() :].strip()
    enonce = _ENONCE_PREFIX.sub("", enonce).strip()
    return enonce, corrige or None


def generate_quiz(
    db: Session,
    user: User,
    domaine: str,
    sous_theme: str | None,
    referentiel: str | None,
) -> QuizAttempt:
    """Generate a quiz exercise for the current user and persist it."""
    if get_domain(domaine) is None:
        raise UnknownDomainError(f"Unknown domain: {domaine}")

    prompt_template = build_domain_prompt(domaine, "generation_exercice")
    prompt = Template(prompt_template).safe_substitute(
        question=f"Generate an exercise on {sous_theme or domaine} for a {user.role if user.role else 'student'} learner.",
        referentiel=referentiel or "not specified",
        profil="étudiant" if user.role == "etudiant" else "professeur",
        sous_theme=sous_theme or "not specified",
        langue=user.langue_preferee,
        historique="None",
    )

    provider = get_llm_provider()
    try:
        raw_response = provider.chat(
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
            max_tokens=1200,
            model=settings.llm_model_generation,
        )
    except Exception as exc:
        logger.warning(
            "Quiz generation LLM failed (domaine=%s, sous_theme=%s): %s",
            domaine,
            sous_theme,
            exc,
        )
        raise QuizGenerationError("Quiz generation failed.") from exc

    if not raw_response or not raw_response.strip():
        logger.warning(
            "Quiz generation LLM returned an empty response (domaine=%s, sous_theme=%s).",
            domaine,
            sous_theme,
        )
        raise QuizGenerationError("Quiz generation failed: empty LLM response.")

    enonce, corrige = _split_quiz_response(raw_response)
    if not enonce:
        # Marker at position 0: keep a placeholder statement so the
        # correction is never leaked through the masked generate response.
        logger.warning(
            "Quiz LLM response has no separable statement (domaine=%s).",
            domaine,
        )
        enonce = (
            "(Énoncé non séparé par le modèle — "
            "la correction reste masquée jusqu'à la soumission.)"
        )
    if corrige is None:
        logger.warning(
            "Quiz generated without separable correction (domaine=%s, sous_theme=%s).",
            domaine,
            sous_theme,
        )

    attempt = QuizAttempt(
        user_id=user.id,
        domaine=domaine,
        sous_theme=sous_theme,
        referentiel=referentiel,
        enonce=enonce,
        corrige=corrige,
        statut="genere",
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def submit_quiz(db: Session, attempt: QuizAttempt, user: User, reponse: str) -> QuizAttempt:
    """Score a submitted answer and generate feedback."""
    if attempt.statut == "corrige":
        raise ValueError("Quiz attempt already submitted.")

    cleaned = reponse.strip() if reponse else ""
    if not cleaned:
        raise ValueError("Answer cannot be empty.")
    attempt.reponse_etudiant = cleaned
    attempt.score = _score_answer(attempt.corrige, cleaned)

    feedback = None
    if attempt.corrige is not None:
        prompt_template = build_domain_prompt(attempt.domaine, "correction")
        prompt = Template(prompt_template).safe_substitute(
            question=(
                f"Exercise: {attempt.enonce}\n\n"
                f"Student answer: {reponse}\n\n"
                f"Correct answer: {attempt.corrige}"
            ),
            referentiel=attempt.referentiel or "not specified",
            profil="étudiant" if user.role == "etudiant" else "professeur",
            sous_theme=attempt.sous_theme or "not specified",
            langue=user.langue_preferee,
            historique="None",
        )
        provider = get_llm_provider()
        try:
            raw_feedback = provider.chat(
                messages=[{"role": "system", "content": prompt}],
                temperature=0.3,
                max_tokens=1200,
                model=settings.llm_model_generation,
            )
            feedback = raw_feedback.strip() if raw_feedback and raw_feedback.strip() else None
        except Exception as exc:
            logger.warning(
                "Quiz feedback LLM failed (attempt_id=%s): %s",
                attempt.id,
                exc,
            )
            feedback = None

    attempt.feedback_corrige = feedback
    attempt.statut = "corrige"
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def list_attempts(db: Session, user_id: int) -> list[QuizAttempt]:
    """Return all quiz attempts for a user ordered newest first."""
    return (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user_id)
        .order_by(QuizAttempt.created_at.desc())
        .all()
    )


def get_attempt(db: Session, attempt_id: int, user_id: int) -> QuizAttempt | None:
    """Return a quiz attempt only if it belongs to the current user."""
    return (
        db.query(QuizAttempt)
        .filter(QuizAttempt.id == attempt_id, QuizAttempt.user_id == user_id)
        .first()
    )
