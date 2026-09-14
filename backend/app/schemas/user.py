"""User-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserBase(BaseModel):
    """Shared user schema."""

    email: str
    role: Literal["etudiant", "professeur"] = "etudiant"
    langue_preferee: str = "fr"
    filiere: str | None = None
    annee: str | None = None
    matieres_enseignees: list[str] | None = None
    etablissement: str | None = None


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or "." not in normalized.split("@")[-1]:
            raise ValueError("Email must be a valid address.")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return value


class UserLogin(BaseModel):
    """Schema for login requests."""

    email: str
    password: str = Field(..., min_length=8)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or "." not in normalized.split("@")[-1]:
            raise ValueError("Email must be a valid address.")
        return normalized


class UserUpdate(BaseModel):
    """Schema for partial profile updates."""

    langue_preferee: str | None = None
    filiere: str | None = None
    annee: str | None = None
    matieres_enseignees: list[str] | None = None
    etablissement: str | None = None


class UserRead(UserBase):
    """Schema returned for authenticated users."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class TokenPair(BaseModel):
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    """Schema for refresh token exchange requests."""

    refresh_token: str
