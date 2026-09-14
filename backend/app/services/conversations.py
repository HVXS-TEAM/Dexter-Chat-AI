"""Conversation persistence service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.conversation import Conversation, Message, UserDomainReferentiel


def create_conversation(db: Session, user_id: int, titre: str | None = None) -> Conversation:
    """Create a new conversation for the given user."""
    conversation = Conversation(
        user_id=user_id,
        titre=titre or "Nouvelle conversation",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(db: Session, conversation_id: int, user_id: int) -> Conversation | None:
    """Return a conversation only if it belongs to the user."""
    return (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )


def list_conversations(db: Session, user_id: int) -> list[Conversation]:
    """List conversations for a user."""
    return db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc()).all()


def add_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
    **kwargs,
) -> Message:
    """Append a message to a conversation."""
    message = Message(conversation_id=conversation_id, role=role, content=content, **kwargs)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def list_messages(db: Session, conversation_id: int) -> list[Message]:
    """List messages for a conversation."""
    return db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()


def update_conversation(db: Session, conversation: Conversation, updates: dict) -> Conversation:
    """Apply partial updates to a conversation."""
    for field, value in updates.items():
        if value is not None:
            setattr(conversation, field, value)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def delete_conversation(db: Session, conversation: Conversation) -> None:
    """Delete a conversation and all associated messages."""
    db.delete(conversation)
    db.commit()


def get_referentiel_for_domain(db: Session, user_id: int, domaine_id: str) -> str | None:
    """Return the selected referential for a domain and user."""
    record = (
        db.query(UserDomainReferentiel)
        .filter(UserDomainReferentiel.user_id == user_id, UserDomainReferentiel.domaine_id == domaine_id)
        .first()
    )
    return record.referentiel if record else None


def set_referentiel_for_domain(db: Session, user_id: int, domaine_id: str, referentiel: str) -> UserDomainReferentiel:
    """Persist the chosen referential per domain."""
    record = (
        db.query(UserDomainReferentiel)
        .filter(UserDomainReferentiel.user_id == user_id, UserDomainReferentiel.domaine_id == domaine_id)
        .first()
    )
    if record is None:
        record = UserDomainReferentiel(user_id=user_id, domaine_id=domaine_id, referentiel=referentiel)
        db.add(record)
    else:
        record.referentiel = referentiel
    db.commit()
    db.refresh(record)
    return record


def build_conversation_context(db: Session, conversation: Conversation) -> str:
    """Build a text block that includes the last conversation context for prompting."""
    parts: list[str] = ["[Conversation context]"]
    if conversation.referentiel_actif:
        parts.append(f"Referentiel actif: {conversation.referentiel_actif}")
    if conversation.resume_md:
        parts.append(f"Resume: {conversation.resume_md}")
    else:
        messages = list_messages(db, conversation.id)
        if messages:
            recent = messages[-10:]
            formatted = "\n".join(
                f"- {item.role}: {item.content}" if item.role in {"user", "assistant"} else item.content
                for item in recent
            )
            parts.append(f"Recent messages:\n{formatted}")
    parts.append("[/Conversation context]")
    return "\n".join(parts)
