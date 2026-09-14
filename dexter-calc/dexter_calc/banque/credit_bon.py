"""Deterministic bank tools for Dexter-Calc: simple interest, final capital, installment.

This module exposes a public functional API for basic credit and savings
calculations, plus a CreditBonCalculator class that implements the Dexter
calculator contract.
"""

from __future__ import annotations

from ..core.calculator import CalculationInput, CalculationOutput, DomainCalculator
from ..core.exceptions import CalculationError
from ..core.validators import valider_montant, valider_taux


def calculer_interet_simple(capital: float, taux: float, duree_mois: int) -> float:
    """Calcule l'interet simple pour un capital, un taux et une duree en mois."""
    capital = valider_montant(capital)
    taux = valider_taux(taux)
    if duree_mois < 0:
        raise CalculationError("La duree en mois ne peut pas etre negative.", code="invalid_duree")
    return round(capital * taux * (duree_mois / 12), 2)


def capital_final(capital: float, taux: float, duree_mois: int) -> float:
    """Capital final apres application d'interets simples."""
    return round(valider_montant(capital) + calculer_interet_simple(capital, valider_taux(taux), duree_mois), 2)


def mensualite_emprunt_simple(capital: float, taux: float, duree_mois: int) -> float:
    """Mensualite simplifiee: amortissement lineaire + interet simple sur capital restant."""
    capital = valider_montant(capital)
    taux = valider_taux(taux)
    if duree_mois <= 0:
        raise CalculationError("La duree en mois doit etre strictement positive.", code="invalid_duree")
    amortissement_mensuel = capital / duree_mois
    interet_mensuel = capital * taux / 12
    return round(amortissement_mensuel + interet_mensuel, 2)


class CreditBonCalculator(DomainCalculator):
    """Outil bancaire : interet simple, capital final, mensualite simplifiee."""

    domain: str = "banque"
    sous_theme: str | None = "credit"
    intention: str | None = "calcul"
    reference_frame: str | None = None
    label: str = "Calcul bancaire simple : interet, capital final, mensualite"
    unit: str | None = "€"

    supported_intentions: tuple[str, ...] = ("calcul", "explique_moi", "pourquoi")
    supported_profiles: tuple[str, ...] = ("etudiant", "professeur")

    def calc(self, input_: CalculationInput) -> CalculationOutput:
        amount = input_.amount if input_.amount is not None else input_.base_amount
        if amount is None:
            raise CalculationError("Un capital ou montant est requis.", code="missing_amount")
        capital = valider_montant(amount)
        taux_raw = input_.tau
        if taux_raw is None:
            taux_raw = input_.rate
        if taux_raw is None:
            taux_raw = input_.rate_fraction
        if taux_raw is None:
            raise CalculationError("Un taux est requis.", code="missing_rate")
        taux = valider_taux(taux_raw)
        duree_mois = input_.period_months or 0
        if duree_mois <= 0:
            raise CalculationError("La duree en mois doit etre strictement positive.", code="invalid_duree")

        interet = calculer_interet_simple(capital, taux, duree_mois)
        final = capital_final(capital, taux, duree_mois)
        mensualite = mensualite_emprunt_simple(capital, taux, duree_mois)

        result = CalculationOutput(
            domain=self.domain,
            sous_theme=self.sous_theme,
            intention=input_.intention or self.intention,
            reference_frame=input_.reference_frame or self.reference_frame,
            result=final,
            label="Capital final (interet simple)",
            unit=self.unit,
            pedagogical_note=f"Interet simple : {interet} € sur {duree_mois} mois. Taux : {round(taux * 100, 2)}%.",
            profile=input_.profile,
            language=input_.language,
        )
        result.extra = {
            "capital_initial": capital,
            "taux": taux,
            "duree_mois": duree_mois,
            "interet_simple": interet,
            "capital_final": final,
            "mensualite_simple": mensualite,
        }
        return result

    def derive(self, input_: CalculationInput) -> CalculationOutput:

        amount = input_.amount if input_.amount is not None else input_.base_amount
        if amount is None:
            raise CalculationError("Un capital ou montant est requis.", code="missing_amount")
        capital = valider_montant(amount)
        taux_raw = input_.tau
        if taux_raw is None:
            taux_raw = input_.rate
        if taux_raw is None:
            taux_raw = input_.rate_fraction
        if taux_raw is None:
            raise CalculationError("Un taux est requis.", code="missing_rate")
        taux = valider_taux(taux_raw)
        duree_mois = input_.period_months or 1
        return CalculationOutput(
            domain=self.domain,
            sous_theme=self.sous_theme,
            intention=input_.intention or self.intention,
            reference_frame=input_.reference_frame or self.reference_frame,
            result=calculer_interet_simple(capital, taux, duree_mois),
            label="Interet simple",
            unit=self.unit,
            pedagogical_note=f"Interet simple sur {capital} € pendant {duree_mois} mois au taux de {round(taux * 100, 2)}%.",
            profile=input_.profile,
            language=input_.language,
        )

    def description(self) -> str:
        return (
            "Outil de calcul bancaire simple : interet simple, capital final, "
            "mensualite simplifiee pour un emprunt. Ce modele est pedagogique et "
            "ne remplace pas une simulation financiere complete avec des formules "
            "d'equite ou des frais annexes."
        )

    def can_handle(self, input_: CalculationInput) -> bool:
        if input_.domain and input_.domain != "banque":
            return False
        if input_.sous_theme and "credit" not in input_.sous_theme:
            return False
        return bool(input_.amount or input_.base_amount)


def register_on(registry: object) -> None:
    """Enregistre le calculateur bancaire dans le registre fourni."""
    if hasattr(registry, "register"):
        registry.register(CreditBonCalculator)
