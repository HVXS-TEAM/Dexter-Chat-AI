"""Message feedback endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.conversation import Message
from app.models.user import User
from app.schemas.conversation import MessageFeedbackUpdate, MessageRead

router = APIRouter(tags=["messages"])


@router.patch("/messages/{message_id}/feedback", response_model=MessageRead)
def update_message_feedback(
    message_id: int,
    payload: MessageFeedbackUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Message:
    """Update the feedback value on a message owned by the current user."""
    message = (
        db.query(Message)
        .join(Message.conversation)
        .filter(Message.id == message_id, Message.conversation.has(user_id=current_user.id))
        .first()
    )
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")

    message.feedback = payload.feedback
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
