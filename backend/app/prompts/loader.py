"""Prompt template loader."""

from __future__ import annotations

from pathlib import Path
from string import Template

TEMPLATES_ROOT = Path(__file__).resolve().parent / "templates"
INTENTIONS = ("explication", "calcul", "cas_pratique", "generation_exercice", "correction")


def _read_template(path: Path) -> str:
    """Read and validate a prompt template file."""
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    try:
        content = path.read_text(encoding="utf-8")
        Template(content).get_identifiers()
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError(f"Prompt template is invalid: {path}") from exc
    if not content.strip():
        raise ValueError(f"Prompt template is empty: {path}")
    return content


def build_domain_prompt(domain_id: str, intention: str) -> str:
    """Concatenate the domain root prompt with its intention instructions."""
    root = _read_template(TEMPLATES_ROOT / domain_id / "root.md")
    selected_intention = intention if intention in INTENTIONS else "explication"
    block = _read_template(TEMPLATES_ROOT / domain_id / f"{selected_intention}.md")
    return f"{root.rstrip()}\n\n{block.strip()}"


def build_rag_context_prompt() -> str:
    """Load the shared prompt used to ground answers in course documents."""
    return _read_template(TEMPLATES_ROOT / "rag_context.md")
