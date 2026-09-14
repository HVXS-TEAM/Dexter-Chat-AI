"""Conversation resume generation service."""

from __future__ import annotations

from string import Template

from sqlalchemy.orm import Session

from app.config import settings
from app.llm import get_llm_provider
from app.models.conversation import Conversation, Message
from app.prompts.loader import _read_template
from app.services.conversations import list_messages


def _format_messages(messages: list[Message]) -> str:
    """Format conversation messages for the resume prompt."""
    return "\n".join(f"- {item.role}: {item.content}" for item in messages)


def generate_resume(db: Session, conversation: Conversation) -> str:
    """Generate a markdown summary of the conversation context."""
    messages = list_messages(db, conversation.id)
    if not messages:
        raise ValueError("Cannot generate a resume for an empty conversation.")

    template_path = _read_template.__globals__["TEMPLATES_ROOT"] / "resume.md"
    prompt_template = template_path.read_text(encoding="utf-8")

    # Determine metadata from the last assistant message if available.
    last_assistant = next((m for m in reversed(messages) if m.role == "assistant"), None)
    domaine = last_assistant.domaine_detecte if last_assistant else None
    sous_theme = last_assistant.sous_theme_detecte if last_assistant else None
    sources_rag = last_assistant.sources_rag if last_assistant else None

    prompt = Template(prompt_template).safe_substitute(
        referentiel=conversation.referentiel_actif or "Non spécifié",
        domaine=domaine or "Non spécifié",
        sous_theme=sous_theme or "Non spécifié",
        langue="fr",
        sources_rag=", ".join(sources_rag) if sources_rag else "Aucune",
        messages=_format_messages(messages),
    )

    provider = get_llm_provider()
    response = provider.chat(
        messages=[{"role": "system", "content": prompt}],
        temperature=0.2,
        max_tokens=800,
        model=settings.llm_model_generation,
    )
    if not response.strip():
        raise ValueError("LLM returned an empty resume.")

    conversation.resume_md = response.strip()
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation.resume_md