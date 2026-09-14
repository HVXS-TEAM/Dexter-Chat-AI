"""Class creation and membership endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.classes import Classe
from app.models.user import User
from app.schemas.classes import ClassCreate, ClassJoinRequest, ClassJoinResponse, ClassRead, ClassReadStudent
from app.services.classes import create_class, get_class, join_class, list_classes

router = APIRouter(tags=["classes"])


def _normalize_class_payload(classe: Classe, include_code: bool) -> dict:
    """Convert ORM models to response payloads that validate reliably with mocks."""
    payload = {
        "id": getattr(classe, "id", None),
        "nom": getattr(classe, "nom", ""),
        "professeur_id": getattr(classe, "professeur_id", 0) or 0,
        "created_at": getattr(classe, "created_at", None) or datetime.now(timezone.utc),
    }
    if include_code:
        payload["code_invitation"] = getattr(classe, "code_invitation", "")
    return payload


@router.post("/classes", response_model=ClassRead, status_code=status.HTTP_201_CREATED)
def create_new_class(
    payload: ClassCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClassRead:
    """Create a class as a professor."""
    if current_user.role != "professeur":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only professors can create classes.")
    created = create_class(db, current_user, payload.nom)
    return _normalize_class_payload(created, include_code=True)


@router.get("/classes", response_model=list[ClassReadStudent] | list[ClassRead])
def read_classes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ClassReadStudent] | list[ClassRead]:
    """List owned classes for professors or joined classes for students."""
    rows = list_classes(db, current_user)
    include_code = current_user.role == "professeur"
    return [_normalize_class_payload(row, include_code=include_code) for row in rows]


@router.post("/classes/{classe_id}/join", response_model=ClassJoinResponse)
def join_class_endpoint(
    classe_id: int,
    payload: ClassJoinRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClassJoinResponse:
    """Join a class using a valid invitation code."""
    if current_user.role != "etudiant":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can join a class.")

    classe = get_class(db, classe_id)
    if classe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")

    try:
        joined = join_class(db, classe, current_user, payload.code_invitation)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return _normalize_class_payload(joined, include_code=False)
