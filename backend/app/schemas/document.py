"""Document API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    """Document payload returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    conversation_id: int
    titre: str
    type_fichier: str
    domaine_associe: str | None
    visibilite: str
    fichier_url: str
    statut_indexation: str
    created_at: datetime


class DocumentVisibilityUpdate(BaseModel):
    """Payload to change document visibility."""

    visibilite: Literal["prive", "partage_classe"]


class DocumentIndexStatus(BaseModel):
    """Document detail with indexing status."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    titre: str
    type_fichier: str
    domaine_associe: str | None
    statut_indexation: str
    nombre_chunks: int = 0
    created_at: datetime
