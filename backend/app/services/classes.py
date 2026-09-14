"""Class management service layer."""

from __future__ import annotations

import secrets

from sqlalchemy.orm import Session

from app.models.classes import Classe, ClasseMembre
from app.models.user import User

INVITATION_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def generate_invitation_code() -> str:
    """Generate a unique invitation code for a new class."""
    return "".join(secrets.choice(INVITATION_ALPHABET) for _ in range(8))


def create_class(db: Session, professeur: User, nom: str) -> Classe:
    """Create a class owned by the professor."""
    classe = Classe(
        professeur_id=professeur.id,
        nom=nom.strip(),
        code_invitation=generate_invitation_code(),
    )
    db.add(classe)
    db.commit()
    db.refresh(classe)
    return classe


def get_class(db: Session, classe_id: int) -> Classe | None:
    """Return a class by identifier."""
    return db.query(Classe).filter(Classe.id == classe_id).first()


def list_classes(db: Session, user: User) -> list[Classe]:
    """List classes for a professor or a joined student."""
    if user.role == "professeur":
        return (
            db.query(Classe)
            .filter(Classe.professeur_id == user.id)
            .order_by(Classe.created_at.desc())
            .all()
        )

    return (
        db.query(Classe)
        .join(ClasseMembre, ClasseMembre.classe_id == Classe.id)
        .filter(ClasseMembre.etudiant_id == user.id)
        .order_by(Classe.created_at.desc())
        .all()
    )


def join_class(db: Session, classe: Classe, etudiant: User, code: str) -> Classe:
    """Join a class if the code is valid and the user is not already a member."""
    actual_code = getattr(classe, "code_invitation", None)
    if not actual_code:
        raise ValueError("Invalid invitation code.")

    normalized_code = code.strip().upper()
    if normalized_code != str(actual_code).strip().upper():
        raise ValueError("Invalid invitation code.")

    existing = (
        db.query(ClasseMembre)
        .filter(ClasseMembre.classe_id == classe.id, ClasseMembre.etudiant_id == etudiant.id)
        .first()
    )
    if existing is not None:
        raise ValueError("Already a member of this class.")

    membership = ClasseMembre(classe_id=classe.id, etudiant_id=etudiant.id)
    db.add(membership)
    db.commit()
    return classe
