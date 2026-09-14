r"""Deterministic VAT (TVA) computations: HT/TTC amounts and collected/deductible/payable VAT.

This module exposes both a low-level functional API (for backward compatibility
and direct usage) and a :class:`TVACalculator` class that conforms to the Dexter
calculator contract.
"""

from __future__ import annotations

from typing import Any

from ..core.calculator import CalculationInput, CalculationOutput, DomainCalculator
from ..core.exceptions import CalculationError
from ..core.validators import valider_montant, valider_taux


def calculer_tva_collectee(montant_ht: float, taux: float) -> float:
    """Calcule la TVA collectee a partir d'un montant HT et d'un taux."""
    montant_ht = valider_montant(montant_ht)
    taux = valider_taux(taux)
    return round(montant_ht * taux, 2)


def calculer_tva_deductible(montant_ht: float, taux: float) -> float:
    """Calcule la TVA deductible a partir d'un montant HT et d'un taux."""
    montant_ht = valider_montant(montant_ht)
    taux = valider_taux(taux)
    return round(montant_ht * taux, 2)


def calculer_tva_a_payer(tva_collectee: float, tva_deductible: float) -> float:
    """Calcule la TVA a payer (positive) ou le credit de TVA (negatif)."""
    tva_collectee = valider_montant(tva_collectee)
    tva_deductible = valider_montant(tva_deductible)
    return round(tva_collectee - tva_deductible, 2)


def calculer_montant_ttc(montant_ht: float, taux: float) -> float:
    """Calcule le montant TTC a partir d'un montant HT et d'un taux."""
    montant_ht = valider_montant(montant_ht)
    taux = valider_taux(taux)
    return round(montant_ht * (1 + taux), 2)


def calculer_montant_ht(montant_ttc: float, taux: float) -> float:
    """Calcule le montant HT a partir d'un montant TTC et d'un taux."""
    montant_ttc = valider_montant(montant_ttc)
    taux = valider_taux(taux)
    return round(montant_ttc / (1 + taux), 2)



class TVACalculator(DomainCalculator):
    """Outil de calcul TVA orienté métier comptable.

    Ce calculateur couvre les sous-thèmes liés à la TVA sur les opérations
    de marchandises et de services : facture, achat, vente, auto-entrepreneur,
    exercice, etc. Il est paramétrable selon le référentiel (OHADA, IFRS,
    plan comptable national, etc.) via l'objet CalculationInput.
    """

    domain: str = "comptabilite"
    sous_theme: str | None = "tva"
    intention: str | None = "calcul"
    reference_frame: str | None = None
    label: str = "Calcul TVA (collectée, déductible, à payer, HT/TTC)"
    unit: str | None = "€"

    supported_intentions: tuple[str, ...] = ("calcul", "explique_moi", "pourquoi")
    supported_profiles: tuple[str, ...] = ("etudiant", "professeur")

    def calc(self, input_: CalculationInput) -> CalculationOutput:
        if input_.amount_ht is None and input_.amount_ttc is None:
            raise CalculationError(
                "Un montant HT ou TTC est requis pour ce calcul.",
                code="missing_amount",
            )
        if input_.tau is None and input_.rate is None and input_.rate_fraction is None:
            raise CalculationError(
                "Un taux de TVA est requis pour ce calcul.",
                code="missing_rate",
            )

        taux = self._resolve_taux(input_)
        result = CalculationOutput(
            domain=self.domain,
            sous_theme=self.sous_theme,
            intention=input_.intention or self.intention,
            reference_frame=input_.reference_frame or self.reference_frame,
            profile=input_.profile,
            language=input_.language,
            label="TVA collectée",
            unit=self.unit,
            pedagogical_note=self._pedagogical_note(taux, input_),
        )

        if input_.amount_ht is not None:
            tva_collectee = calculer_tva_collectee(input_.amount_ht, taux)
            tva_deductible = calculer_tva_deductible(input_.amount_ht, taux)
            result.result = tva_collectee
            result.extra = {
                "taux": taux,
                "montant_ht": input_.amount_ht,
                "tva_collectee": tva_collectee,
                "tva_deductible": tva_deductible,
                "tva_a_payer": calculer_tva_a_payer(tva_collectee, tva_deductible),
                "montant_ttc": calculer_montant_ttc(input_.amount_ht, taux),
                "montant_ht_from_ttc": (calculer_montant_ht(input_.amount_ttc, taux) if input_.amount_ttc is not None else None),
            }
            result.label = "TVA collectée sur HT"
        else:
            # Cas TTC -> HT
            ht = calculer_montant_ht(input_.amount_ttc, taux)
            tva_collectee = calculer_tva_collectee(ht, taux)
            result.result = ht
            result.label = "Montant HT"
            result.extra = {
                "taux": taux,
                "montant_ttc": input_.amount_ttc,
                "montant_ht": ht,
                "tva_collectee": tva_collectee,
            }

        return result

    def derive(self, input_: CalculationInput) -> CalculationOutput:
        # Permet d'obtenir rapidement le montant TTC depuis HT si l'input est HT
        if input_.amount_ht is None:
            raise CalculationError("Un montant HT est requis pour le calcul dérivé.", code="missing_amount")
        taux = self._resolve_taux(input_)
        return CalculationOutput(
            domain=self.domain,
            sous_theme=self.sous_theme,
            intention=input_.intention or self.intention,
            reference_frame=input_.reference_frame or self.reference_frame,
            result=calculer_montant_ttc(input_.amount_ht, taux),
            label="Montant TTC",
            unit=self.unit,
            pedagogical_note=self._pedagogical_note(taux, input_),
        )

    def description(self) -> str:
        return (
            "Outil de calcul de la TVA : montant collecté, montant déductible, "
            "TVA à payer ou crédit de TVA, conversion HT ↔ TTC. "
            "Selon le référentiel comptable retenu, les règles de facturation, "
            "d'autolimitation ou de régularisation peuvent varier."
        )

    def can_handle(self, input_: CalculationInput) -> bool:
        if input_.domain and input_.domain != "comptabilite":
            return False
        return input_.amount_ht is not None or input_.amount_ttc is not None

    def _resolve_taux(self, input_: CalculationInput) -> float:
        taux = input_.tau or input_.rate or input_.rate_fraction
        if taux is None:
            raise CalculationError("Un taux de TVA est requis.", code="missing_rate")
        return valider_taux(taux)

    def _pedagogical_note(self, taux: float, input_: CalculationInput) -> str:
        taux_pct = round(taux * 100, 2)
        return (
            f"Le taux de TVA appliqué est de {taux_pct}%. "
            f"Si vous avez besoin d'adapter ce taux au référentiel retenu "
            f"({input_.reference_frame or 'non précisé'}), précisez-le dans la question."
        )


def register_on(registry: Any) -> None:
    """Enregistre le calculateur TVA dans le registre fourni."""
    if hasattr(registry, "register"):
        registry.register(TVACalculator)
