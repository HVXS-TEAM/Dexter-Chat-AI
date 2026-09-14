"""Class and membership models for Dexter."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class Classe(Base):
    """A class created by a professor and joined by students."""

    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    professeur_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    code_invitation: Mapped[str] = mapped_column(String(12), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    professeur: Mapped["User"] = relationship(back_populates="classes_enseignees")
    membres: Mapped[list["ClasseMembre"]] = relationship(
        back_populates="classe",
        cascade="all, delete-orphan",
    )
    etudiants: Mapped[list["User"]] = relationship(
        secondary="classe_membres",
        back_populates="classes_inscrites",
        overlaps="membres",
        viewonly=True,
    )


class ClasseMembre(Base):
    """A membership link between a class and a student."""

    __tablename__ = "classe_membres"

    classe_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True
    )
    etudiant_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    classe: Mapped["Classe"] = relationship(back_populates="membres")
