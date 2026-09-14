"""Conversation and message models for Dexter."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class Conversation(Base):
    """A persistent chat session belonging to a user."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    titre: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    referentiel_actif: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resume_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class Message(Base):
    """A single message inside a conversation."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    domaine_detecte: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sous_theme_detecte: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mode_utilise: Mapped[str] = mapped_column(String(20), nullable=False, default="explique_moi")
    sources_rag: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class UserDomainReferentiel(Base):
    """The latest referential chosen by a user for a domain."""

    __tablename__ = "user_domain_referentiels"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True, nullable=False)
    domaine_id: Mapped[str] = mapped_column(String(50), primary_key=True, nullable=False)
    referentiel: Mapped[str] = mapped_column(String(50), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
