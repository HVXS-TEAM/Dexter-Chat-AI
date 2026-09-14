from __future__ import annotations

import hashlib
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import (
    UserCreate,
    UserResponse,
    UserProfileUpdate,
    Token,
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def register(self, payload: UserCreate) -> Token:
        existing = self.get_user_by_email(payload.email)
        if existing:
            raise ValueError("Un utilisateur avec cet email existe deja")

        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=payload.role or "etudiant",
            langue_preferee=payload.langue_preferee or "fr",
            filiere=payload.filiere,
            annee=payload.annee,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return Token(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    def login(self, email: str, password: str) -> Token:
        user = self.get_user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Email ou mot de passe incorrect")

        return Token(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    def get_profile(self, user_id: int) -> UserResponse:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Utilisateur non trouve")
        return UserResponse.model_validate(user)

    def update_profile(self, user_id: int, payload: UserProfileUpdate) -> UserResponse:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Utilisateur non trouve")

        update_data = payload.model_dump(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            update_data["password_hash"] = hash_password(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return UserResponse.model_validate(user)

    def refresh(self, refresh_token: str) -> Token:
        from app.schemas.auth import decode_token
        data = decode_token(refresh_token)
        if data is None or data.user_id is None:
            raise ValueError("Refresh token invalide")
        return Token(
            access_token=create_access_token(data.user_id),
            refresh_token=create_refresh_token(data.user_id),
        )
