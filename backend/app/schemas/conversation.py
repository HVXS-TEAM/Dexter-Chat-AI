"""Conversation-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    """Payload used to create a conversation."""

    titre: str | None = None


class ConversationUpdate(BaseModel):
    """Payload used to update a conversation."""

    titre: str | None = None
    referentiel_actif: str | None = None


class ConversationRead(BaseModel):
    """Basic conversation payload."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    titre: str
    referentiel_actif: str | None
    resume_md: str | None
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    """Payload used to create a message in a conversation."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)
    domaine_detecte: str | None = None
    sous_theme_detecte: str | None = None
    mode_utilise: str = "explique_moi"
    sources_rag: list[str] | None = None


class MessageRead(BaseModel):
    """Message payload returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str
    content: str
    domaine_detecte: str | None
    sous_theme_detecte: str | None
    mode_utilise: str
    sources_rag: list[str] | None
    created_at: datetime


class ConversationDetailRead(ConversationRead):
    """Conversation payload including its messages."""

    messages: list[MessageRead] = []


class UserDomainReferentielRead(BaseModel):
    """Persisted referential chosen by a user for a domain."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    domaine_id: str
    referentiel: str
    updated_at: datetime
