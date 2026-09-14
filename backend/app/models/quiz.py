"""Quiz attempt model for Dexter."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class QuizAttempt(Base):
    """A generated exercise and its correction for a user."""

    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    domaine: Mapped[str] = mapped_column(String(50), nullable=False)
    sous_theme: Mapped[str | None] = mapped_column(String(100), nullable=True)
    referentiel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    enonce: Mapped[str] = mapped_column(Text, nullable=False)
    corrige: Mapped[str | None] = mapped_column(Text, nullable=True)
    reponse_etudiant: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback_corrige: Mapped[str | None] = mapped_column(Text, nullable=True)
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="genere")
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

    user: Mapped["User"] = relationship(back_populates="quiz_attempts")
