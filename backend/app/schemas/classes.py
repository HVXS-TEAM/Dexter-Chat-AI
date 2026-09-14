"""Class-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClassCreate(BaseModel):
    """Payload used to create a class."""

    nom: str = Field(..., min_length=1)

    @field_validator("nom")
    @classmethod
    def validate_nom(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name must not be empty.")
        return normalized


class ClassRead(BaseModel):
    """Class payload returned to the professor owner."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    professeur_id: int
    code_invitation: str
    created_at: datetime


class ClassReadStudent(BaseModel):
    """Class payload returned to a student member."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    professeur_id: int
    created_at: datetime


class ClassJoinRequest(BaseModel):
    """Invitation code for joining a class."""

    code_invitation: str = Field(..., min_length=1)

    @field_validator("code_invitation")
    @classmethod
    def validate_code(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Invitation code must not be empty.")
        return normalized


class ClassJoinResponse(ClassReadStudent):
    """Class payload returned after a successful join."""

    pass
