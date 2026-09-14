"""User model for Dexter."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class User(Base):
    """Application user profile."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="etudiant")
    langue_preferee: Mapped[str] = mapped_column(String(20), nullable=False, default="fr")
    filiere: Mapped[str | None] = mapped_column(String(255), nullable=True)
    annee: Mapped[str | None] = mapped_column(String(50), nullable=True)
    matieres_enseignees: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    etablissement: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    classes_enseignees: Mapped[list["Classe"]] = relationship(
        back_populates="professeur",
        cascade="all, delete-orphan",
    )
    classes_inscrites: Mapped[list["Classe"]] = relationship(
        secondary="classe_membres",
        back_populates="etudiants",
        viewonly=True,
    )
