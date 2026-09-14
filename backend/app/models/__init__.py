"""Database models package for Dexter."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


from .classes import Classe, ClasseMembre
from .conversation import Conversation, Message, UserDomainReferentiel
from .document import Document, DocumentChunk
from .quiz import QuizAttempt
from .user import User

__all__ = [
    "Base",
    "User",
    "Classe",
    "ClasseMembre",
    "Conversation",
    "Message",
    "UserDomainReferentiel",
    "Document",
    "DocumentChunk",
    "QuizAttempt",
]
