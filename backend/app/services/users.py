"""User service layer."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.auth.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user_by_email(db: Session, email: str) -> User | None:
    """Fetch a user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Fetch a user by identifier."""
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Validate credentials for login."""
    user = get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user record with a hashed password."""
    user = User(
        email=user_data.email.lower(),
        password_hash=hash_password(user_data.password),
        role=user_data.role.lower(),
        langue_preferee=user_data.langue_preferee or "fr",
        filiere=user_data.filiere,
        annee=user_data.annee,
        matieres_enseignees=user_data.matieres_enseignees,
        etablissement=user_data.etablissement,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, updates: UserUpdate | dict) -> User:
    """Apply validated profile updates to a user."""
    if isinstance(updates, UserUpdate):
        payload = updates.model_dump(exclude_unset=True)
    else:
        payload = updates

    for field, value in payload.items():
        if value is not None:
            setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
