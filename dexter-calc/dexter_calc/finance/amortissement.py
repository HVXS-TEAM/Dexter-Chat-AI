"""Deterministic finance tools for Dexter-Calc: linear amortization and related helpers.

This module exposes a public functional API for depreciation / amortization
calculations, plus an AmortissementLineaireCalculator class that implements
the Dexter calculator contract.
"""

from __future__ import annotations

from ..core.calculator import CalculationInput, CalculationOutput, DomainCalculator
from ..core.exceptions import CalculationError
from ..core.validators import valider_montant


def valider_annee(annee: int) -> int:
    """Valide une duree d'amortissement en annees."""
    if not isinstance(annee, int) or isinstance(annee, bool):
        raise CalculationError("La duree d'amortissement doit etre un entier positif.", code="invalid_year")
    if annee <= 0:
        raise CalculationError("La duree d'amortissement doit etre strictement positive.", code="invalid_year")
    return annee


def calculer_dotation_lineaire(valeur_a_amortir: float, duree: int) -> float:
    """Calcule la dotation d'amortissement lineaire annuelle."""
    valeur = valider_montant(valeur_a_amortir)
    duree = valider_annee(duree)
    return round(valeur / duree, 2)


def calculer_valeur_residuelle(valeur_initiale: float, duree: int, annees_ecoulees: int) -> float:
    """Calcule la valeur residuelle (valeur nette comptable) apres un certain
    nombre d'annees d'amortissement."""
    valeur = valider_montant(valeur_initiale)
    duree = valider_annee(duree)
    if annees_ecoulees < 0:
        raise CalculationError("Le nombre d'annees ecoulees ne peut pas etre negatif.", code="invalid_annee")
    if annees_ecoulees > duree:
        annees_ecoulees = duree
    dotation = calculer_dotation_lineaire(valeur, duree)
    return round(max(valeur - dotation * annees_ecoulees, 0.0), 2)


class AmortissementLineaireCalculator(DomainCalculator):
    """Outil de calcul financier: amortissement lineaire d'un actif immobilise."""

    domain: str = "finance"
    sous_theme: str | None = "amortissement"
    intention: str | None = "calcul"
    reference_frame: str | None = None
    label: str = "Calcul de l'amortissement lineaire"
    unit: str | None = "€"

    supported_intentions: tuple[str, ...] = ("calcul", "explique_moi", "pourquoi")
    supported_profiles: tuple[str, ...] = ("etudiant", "professeur")

    def calc(self, input_: CalculationInput) -> CalculationOutput:
        montant = input_.amount if input_.amount is not None else input_.base_amount
        if montant is None:
            raise CalculationError("Une valeur d'origine (amount ou base_amount) est requise.", code="missing_amount")
        if input_.periods is None:
            raise CalculationError("Une duree d'amortissement (periods) est requise.", code="missing_duration")
        if input_.period_years is None:
            raise CalculationError(
                "Un nombre d'annees ecoulees (period_years) est requis.",
                code="missing_period_years",
            )
        annees_raw = float(input_.period_years)
        if annees_raw != int(annees_raw):
            raise CalculationError("Le nombre d'annees ecoulees doit etre un entier.", code="invalid_annees")
        annees = int(annees_raw)

        valeur = valider_montant(montant)
        duree = valider_annee(input_.periods)
        dotation = calculer_dotation_lineaire(valeur, duree)
        residuelle = calculer_valeur_residuelle(valeur, duree, annees)

        result = CalculationOutput(
            domain=self.domain,
            sous_theme=self.sous_theme,
            intention=input_.intention or self.intention,
            reference_frame=input_.reference_frame or self.reference_frame,
            result=residuelle,
            label="Valeur residuelle",
            unit=self.unit,
            pedagogical_note=f"Dotation annuelle lineaire : {dotation} €. Valeur initiale : {valeur} €. Duree : {duree} annees.",
            profile=input_.profile,
            language=input_.language,
        )
        result.extra = {
            "valeur_initiale": valeur,
            "duree": duree,
            "annees_ecoulees": annees,
            "dotation_annuelle": dotation,
            "valeur_residuelle": residuelle,
            "total_amorti": round(dotation * annees, 2),
            "reste_a_amortir": round(residuelle, 2),
        }
        return result

    def derive(self, input_: CalculationInput) -> CalculationOutput:
        montant = input_.amount if input_.amount is not None else input_.base_amount
        if montant is None:
            raise CalculationError("Une valeur d'origine (amount ou base_amount) est requise.", code="missing_amount")
        if input_.periods is None:
            raise CalculationError("Une duree d'amortissement (periods) est requise.", code="missing_duration")
        valeur = valider_montant(montant)
        duree = valider_annee(input_.periods)
        dotation = calculer_dotation_lineaire(valeur, duree)
        return CalculationOutput(
            domain=self.domain,
            sous_theme=self.sous_theme,
            intention=input_.intention or self.intention,
            reference_frame=input_.reference_frame or self.reference_frame,
            result=dotation,
            label="Dotation d'amortissement annuelle",
            unit=self.unit,
            pedagogical_note=f"Dotation lineaire annuelle pour un actif de {valeur} € sur {duree} annees.",
            profile=input_.profile,
            language=input_.language,
        )

    def description(self) -> str:
        return (
            "Outil de calcul de l'amortissement lineaire d'un actif immobilise : "
            "dotation annuelle, valeur residuelle apres N annees, montant total "
            "amorti. Ce calcul est independant du referentiel comptable precis, "
            "mais peut etre adapte selon les regles du plan comptable retenu."
        )

    def can_handle(self, input_: CalculationInput) -> bool:
        if input_.domain and input_.domain != "finance":
            return False
        if input_.sous_theme and "amortissement" not in input_.sous_theme:
            return False
        return bool(input_.amount or input_.base_amount)


def register_on(registry: object) -> None:
    """Enregistre le calculateur d'amortissement dans le registre fourni."""
    if hasattr(registry, "register"):
        registry.register(AmortissementLineaireCalculator)
