"""Document upload and management endpoints."""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import settings
from app.db.session import get_db
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentIndexStatus, DocumentRead, DocumentVisibilityUpdate
from app.services.conversations import get_conversation
from app.services.rag_service import index_document

router = APIRouter(tags=["documents"])
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".png", ".jpg", ".jpeg", ".txt", ".md"}

_logger = logging.getLogger(__name__)


def _upload_root() -> Path:
    """Return the backend upload directory and create it if needed."""
    root = Path(__file__).resolve().parents[2] / settings.upload_dir
    root.mkdir(parents=True, exist_ok=True)
    return root


def _get_owned_document(db: Session, document_id: int, user_id: int) -> Document | None:
    """Return a document only when it belongs to the user."""
    return db.query(Document).filter(Document.id == document_id, Document.owner_id == user_id).first()


@router.post(
    "/conversations/{conversation_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    conversation_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Document:
    """Upload and synchronously index a document in a conversation."""
    conversation = get_conversation(db, conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported document type.")
    file_bytes = file.file.read()
    stored_name = f"{uuid4().hex}_{Path(file.filename or 'document').name}"
    target = _upload_root() / stored_name
    target.write_bytes(file_bytes)
    document = Document(
        owner_id=current_user.id,
        conversation_id=conversation.id,
        titre=file.filename or stored_name,
        type_fichier=suffix[1:],
        fichier_url=str(target.relative_to(Path(__file__).resolve().parents[2])),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    try:
        return index_document(db, document, file_bytes)
    except Exception as exc:
        _logger.exception(
            "Document indexing failed for document id=%s (%s)", document.id, document.titre
        )
        document.statut_indexation = "erreur"
        db.add(document)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Document indexing failed."
        ) from exc


@router.get("/conversations/{conversation_id}/documents", response_model=list[DocumentRead])
def list_documents(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Document]:
    """List documents owned by the current user in a conversation."""
    if get_conversation(db, conversation_id, current_user.id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return (
        db.query(Document)
        .filter(Document.conversation_id == conversation_id, Document.owner_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )


@router.get("/documents/{document_id}", response_model=DocumentIndexStatus)
def read_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentIndexStatus:
    """Return document indexing status for its owner."""
    document = _get_owned_document(db, document_id, current_user.id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return DocumentIndexStatus(
        id=document.id,
        titre=document.titre,
        type_fichier=document.type_fichier,
        domaine_associe=document.domaine_associe,
        statut_indexation=document.statut_indexation,
        nombre_chunks=len(document.chunks),
        created_at=document.created_at,
    )


@router.patch("/documents/{document_id}/visibility", response_model=DocumentRead)
def update_document_visibility(
    document_id: int,
    payload: DocumentVisibilityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Document:
    """Change document visibility for a professor-owned document."""
    document = _get_owned_document(db, document_id, current_user.id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    if current_user.role != "professeur":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only professors can share documents.")
    document.visibilite = payload.visibilite
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a document and its indexed chunks."""
    document = _get_owned_document(db, document_id, current_user.id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    path = Path(__file__).resolve().parents[2] / document.fichier_url
    db.delete(document)
    db.commit()
    if path.exists():
        path.unlink()
