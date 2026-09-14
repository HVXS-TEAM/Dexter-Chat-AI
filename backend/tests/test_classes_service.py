"""Service-layer tests for the classes module (real execution, in-memory SQLite)."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Classe, ClasseMembre
from app.services.classes import (
    create_class,
    generate_invitation_code,
    join_class,
    list_classes,
)

INVITATION_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(
        bind=engine, tables=[Classe.__table__, ClasseMembre.__table__]
    )
    session = Session(bind=engine)
    yield session
    session.close()
    engine.dispose()


def _user(user_id: int, role: str):
    return type("User", (), {"id": user_id, "role": role})()


def test_invitation_code_length_and_alphabet():
    code = generate_invitation_code()
    assert len(code) == 8
    assert set(code) <= set(INVITATION_ALPHABET)


def test_create_class_generates_code_and_trims_name(db):
    professeur = _user(1, "professeur")
    classe = create_class(db, professeur, "  Mathématiques  ")
    assert classe.id is not None
    assert classe.nom == "Mathématiques"
    assert classe.professeur_id == 1
    assert len(classe.code_invitation) == 8
    assert set(classe.code_invitation) <= set(INVITATION_ALPHABET)


def test_join_class_success_persists_membership(db):
    professeur = _user(1, "professeur")
    classe = create_class(db, professeur, "Maths")
    etudiant = _user(2, "etudiant")

    joined = join_class(db, classe, etudiant, classe.code_invitation.lower())

    assert joined.id == classe.id
    row = (
        db.query(ClasseMembre)
        .filter(
            ClasseMembre.classe_id == classe.id,
            ClasseMembre.etudiant_id == 2,
        )
        .one()
    )
    assert row.joined_at is not None


def test_join_class_wrong_code_raises(db):
    professeur = _user(1, "professeur")
    classe = create_class(db, professeur, "Maths")
    etudiant = _user(2, "etudiant")

    with pytest.raises(ValueError, match="Invalid invitation code."):
        join_class(db, classe, etudiant, "ZZZZZZZZ")


def test_join_class_already_member_raises(db):
    professeur = _user(1, "professeur")
    classe = create_class(db, professeur, "Maths")
    etudiant = _user(2, "etudiant")
    join_class(db, classe, etudiant, classe.code_invitation)

    with pytest.raises(ValueError, match="Already a member of this class."):
        join_class(db, classe, etudiant, classe.code_invitation)


def test_list_classes_student_returns_only_joined(db):
    professeur = _user(1, "professeur")
    maths = create_class(db, professeur, "Maths")
    physique = create_class(db, professeur, "Physique")
    etudiant = _user(2, "etudiant")
    join_class(db, maths, etudiant, maths.code_invitation)

    seen = list_classes(db, etudiant)
    assert [c.id for c in seen] == [maths.id]


def test_list_classes_professor_returns_owned(db):
    professeur = _user(1, "professeur")
    maths = create_class(db, professeur, "Maths")
    physique = create_class(db, professeur, "Physique")

    seen = list_classes(db, professeur)
    assert {c.id for c in seen} == {maths.id, physique.id}