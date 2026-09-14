"""Core abstractions for Dexter-Calc: inputs, outputs, base calculator contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CalculationInput:
    """Inputs explicites pour un calcul métier.

    Chaque calcul définit ses propres attributs via des sous-classes ou
    l'usage direct des champs generiques. Le champ ``domain`` est optionnel
    pour permettre une utilisation centralisée sans forcer la presence d'une
    classe par outil dans tous les contextes.
    """

    domain: str | None = None
    sous_theme: str | None = None
    intention: str | None = None
    reference_frame: str | None = None
    profile: str | None = None
    language: str | None = None
    # Champs numeriques generiques, interprets par l'outil concret.
    amount_ht: float | None = None
    amount_ttc: float | None = None
    amount: float | None = None
    tau: float | None = None
    rate: float | None = None
    rate_fraction: float | None = None
    period_years: float | None = None
    period_months: float | None = None
    periods: int | None = None
    flow: float | None = None
    flows: list[float] | None = None
    discount_rate: float | None = None
    spot_rate: float | None = None
    forward_rate: float | None = None
    base_amount: float | None = None
    start_value: float | None = None
    comment: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class CalculationOutput:
    """Resultat explicite d'un outil de calcul, avec contexte pedagogique."""

    domain: str
    sous_theme: str | None = None
    intention: str | None = None
    reference_frame: str | None = None
    result: float = 0.0
    label: str = ""
    unit: str | None = None
    precision_note: str | None = None
    pedagogical_note: str | None = None
    profile: str | None = None
    language: str | None = None
    display_currency: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class DomainCalculator:
    """Contrat métier commun à tous les outils de calcul Dexter.

    Chaque calcul est exprimé autour de son intention métier réelle, pas
    autour d'une signature générique unique. Les attributs publics utilisés
    dans les outils sont les méthodes et propriétés plutôt qu'une signature
    unique.
    """

    domain: str = ""
    sous_theme: str | None = None
    intention: str | None = None
    reference_frame: str | None = None
    label: str = ""
    unit: str | None = None
    supported_intentions: tuple[str, ...] = ()
    supported_profiles: tuple[str, ...] = ("etudiant", "professeur")

    def calc(self, input_: CalculationInput) -> CalculationOutput:
        """Calcule et retourne le résultat du calcul demandé."""
        raise NotImplementedError

    def derive(self, input_: CalculationInput) -> CalculationOutput:
        """Calcul de forme derivee (inverse, complementaire, récapitulatif) quand utile."""
        raise NotImplementedError

    def description(self) -> str:
        """Description pédagogique courte de l'outil, utilisable dans l'interface chat."""
        return ""

    def can_handle(self, input_: CalculationInput) -> bool:
        """Détermine si l'outil peut traiter l'input en fonction de son intention, domaine, référentiel, profil et langue."""
        return False
