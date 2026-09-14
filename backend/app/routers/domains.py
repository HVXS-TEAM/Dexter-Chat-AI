"""Public domain catalogue router."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.domains.loader import list_domains

router = APIRouter(prefix="/domains", tags=["domains"])


class DomainOut(BaseModel):
    """Public representation of a configured domain."""

    id: str
    label: str
    keywords: list[str] = []
    sous_themes: list[str] = []
    referentiels: list[str] = []


@router.get("", response_model=list[DomainOut])
def get_domains() -> list[DomainOut]:
    """Return the configured domains (static catalogue, PRD §12.4)."""
    return [
        DomainOut(
            id=domain["id"],
            label=domain["label"],
            keywords=domain.get("keywords", []),
            sous_themes=domain.get("sous_themes", []),
            referentiels=domain.get("referentiels", []),
        )
        for domain in list_domains()
    ]
