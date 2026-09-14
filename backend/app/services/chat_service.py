"""Pedagogical answer generation service."""

from __future__ import annotations

from string import Template

from app.config import settings
from app.llm import get_llm_provider
from app.models.user import User
from app.prompts.loader import build_domain_prompt, build_rag_context_prompt
from app.schemas.chat import ClassificationResult


def generate_answer(
    question: str,
    classification: ClassificationResult,
    user: User,
    history_context: str | None = None,
    rag_context: str | None = None,
) -> str:
    """Generate a pedagogical answer using the classified domain prompt."""
    if not classification.domaine:
        raise ValueError("A configured domain is required for answer generation.")

    prompt_template = build_domain_prompt(classification.domaine, classification.intention)
    prompt = Template(prompt_template).safe_substitute(
        question=question,
        referentiel=classification.referentiel or "not specified",
        profil="étudiant" if user.role == "etudiant" else "professeur",
        sous_theme=classification.sous_theme or "not specified",
        langue=classification.langue or user.langue_preferee,
        historique=history_context or "None",
    )
    if rag_context:
        rag_template = build_rag_context_prompt()
        rag_prompt = Template(rag_template).safe_substitute(
            chunks=rag_context,
            question=question,
            langue=classification.langue or user.langue_preferee,
            profil="étudiant" if user.role == "etudiant" else "professeur",
        )
        prompt = f"{prompt}\n\n{rag_prompt}"

    provider = get_llm_provider()
    response = provider.chat(
        messages=[{"role": "system", "content": prompt}],
        temperature=0.3,
        max_tokens=1200,
        model=settings.llm_model_generation,
    )
    if not response.strip():
        raise ValueError("LLM returned an empty answer.")
    return response.strip()
