"""Domain configuration loader."""

from __future__ import annotations

import json
from pathlib import Path

DOMAIN_FILE = Path(__file__).resolve().with_name("domains.json")


def _load_raw_domains() -> list[dict]:
    """Load the domain configuration file as structured JSON."""
    if not DOMAIN_FILE.exists():
        raise FileNotFoundError(f"Domain configuration file not found: {DOMAIN_FILE}")

    try:
        with DOMAIN_FILE.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Domain configuration file is corrupted: {DOMAIN_FILE}") from exc

    if not isinstance(payload, list) or not payload:
        raise ValueError("Domain configuration file is empty or invalid.")

    return payload


def list_domains() -> list[dict]:
    """Return the list of configured domains."""
    return _load_raw_domains()


def get_domain(domain_id: str | None) -> dict | None:
    """Return a configured domain by its identifier."""
    if not domain_id:
        return None
    for domain in _load_raw_domains():
        if domain.get("id") == domain_id:
            return domain
    return None


def domain_prompt_context() -> str:
    """Build a deterministic prompt section describing the configured domains."""
    domains = list_domains()
    sections: list[str] = []
    for domain in domains:
        section = (
            f"- {domain['id']}: label={domain['label']}; "
            f"keywords={', '.join(domain.get('keywords', []))}; "
            f"subthemes={', '.join(domain.get('sous_themes', []))}; "
            f"referentiels={', '.join(domain.get('referentiels', []))}"
        )
        sections.append(section)
    return "\n".join(sections)
