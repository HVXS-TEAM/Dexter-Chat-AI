"""Conversation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetailRead,
    ConversationRead,
    ConversationUpdate,
    MessageCreate,
    MessageRead,
)
from app.services.conversations import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    update_conversation,
)
from app.services.resume_service import generate_resume

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationRead])
def read_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Conversation]:
    """List all conversations for the logged-in user."""
    return list_conversations(db, current_user.id)


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_new_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Conversation:
    """Create a new conversation."""
    title = payload.titre.strip() if payload.titre else "Nouvelle conversation"
    conversation = create_conversation(db, current_user.id, title)
    return conversation


@router.get("/{conversation_id}", response_model=ConversationDetailRead)
def read_conversation_detail(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Conversation:
    """Read a conversation and its messages."""
    conversation = get_conversation(db, conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return conversation


@router.patch("/{conversation_id}", response_model=ConversationRead)
def patch_conversation(
    conversation_id: int,
    payload: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Conversation:
    """Update a conversation title or referential."""
    conversation = get_conversation(db, conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    updates = payload.model_dump(exclude_unset=True)
    return update_conversation(db, conversation, updates)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a conversation owned by the current user."""
    conversation = get_conversation(db, conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    delete_conversation(db, conversation)


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
def list_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    """List all messages in a conversation."""
    conversation = get_conversation(db, conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return conversation.messages


@router.post("/{conversation_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
def add_message_to_conversation(
    conversation_id: int,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> object:
    """Create a message inside a conversation."""
    conversation = get_conversation(db, conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return add_message(
        db,
        conversation_id,
        payload.role,
        payload.content,
        domaine_detecte=payload.domaine_detecte,
        sous_theme_detecte=payload.sous_theme_detecte,
        mode_utilise=payload.mode_utilise,
        sources_rag=payload.sources_rag,
    )


@router.post("/{conversation_id}/resume", response_model=ConversationRead)
def generate_conversation_resume(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Conversation:
    """Generate a markdown resume of the conversation context."""
    conversation = get_conversation(db, conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    try:
        generate_resume(db, conversation)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Resume generation failed.") from exc
    return conversation