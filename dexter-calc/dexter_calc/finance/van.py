"""Deterministic net present value, internal rate and related finance tools.

This module exposes a public functional API for VAN and discounting, plus a
VANChatCalculator class that implements the Dexter calculator contract.
"""

from __future__ import annotations

from typing import Sequence

from ..core.calculator import CalculationInput, CalculationOutput, DomainCalculator
from ..core.exceptions import CalculationError
from ..core.validators import valider_montant, valider_taux


def calculer_flux_actualise(flux: float, taux_actualisation: float, periode: int) -> float:
    """Actualise un flux unique a une periode donnee."""
    flux = valider_montant(flux)
    taux_actualisation = valider_taux(taux_actualisation)
    if periode < 0:
        raise CalculationError("La periode doit etre >= 0.", code="invalid_period")
    return flux / (1 + taux_actualisation) ** periode


def calculer_van_flux(
    flux_initial: float,
    flux_exploitations: Sequence[float],
    taux_actualisation: float,
) -> float:
    """VAN a partir d'un flux initial et d'une sequence de flux d'exploitation."""
    flux_initial = valider_montant(flux_initial)
    taux_actualisation = valider_taux(taux_actualisation)

    van = -flux_initial
    for index, flux in enumerate(flux_exploitations, start=1):
        van += calculer_flux_actualise(flux, taux_actualisation, index)

    return round(van, 4)


def calcul_van(
    flux_initial: float,
    flux_exploitations: Sequence[float],
    taux_actualisation: float,
) -> float:
    """Alias historique de :func:`calculer_van_flux` (nom court attendu par
    les premiers importeurs du module)."""
    return calculer_van_flux(flux_initial, flux_exploitations, taux_actualisation)


def calculer_ica(
    flux_annuel_net: float,
    investissement: float,
    taux_actualisation: float = 0.1,
) -> float:
    """Indice de rentabilite simple : VAN d'un flux unique sur un an,
    actualisee a ``taux_actualisation``, divisee par l'investissement."""
    investissement = valider_montant(investissement)
    if investissement == 0:
        raise CalculationError(
            "L'investissement ne peut pas etre nul pour calculer l'ICA.",
            code="invalid_investment",
        )
    van = calculer_van_flux(0.0, [flux_annuel_net], taux_actualisation)
    return round(van / investissement, 4)


def calculer_tir_simple(flux_initial: float, flux_exploitations: Sequence[float]) -> float:
    """Estimation pedagogique du TIR (taux de rentabilite interne) par
    recherche dichotomique sur [0 ; 1].

    Leve une ``CalculationError`` explicite si la VAN ne change pas de signe
    dans cet intervalle (pas de TIR trouve) — jamais de NaN silencieux.
    """
    flux_initial = valider_montant(flux_initial)
    if not flux_exploitations:
        raise CalculationError(
            "Aucun flux d'exploitation fourni pour le calcul du TIR.",
            code="missing_flows",
        )

    def van_pour(t: float) -> float:
        return calculer_van_flux(flux_initial, flux_exploitations, t)

    lo, hi = 0.0, 1.0
    if van_pour(lo) * van_pour(hi) >= 0:
        raise CalculationError(
            "Pas de TIR trouve dans l'intervalle [0 ; 1] : la VAN n'y change pas de signe.",
            code="no_tir_in_range",
        )

    tir = 0.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if van_pour(mid) * van_pour(lo) <= 0:
            hi = mid
        else:
            lo = mid
        tir = (lo + hi) / 2
    return round(tir, 6)


class VANChatCalculator(DomainCalculator):
    """Outil de calcul finance : VAN et ICA (indice de rentabilite simple)."""

    domain: str = "finance"
    sous_theme: str | None = "van"
    intention: str | None = "calcul"
    label: str = "Calcul VAN / ICA"
    unit: str | None = "€"

    def calc(self, input_: CalculationInput) -> CalculationOutput:
        if input_.base_amount is None or not input_.flows:
            raise CalculationError("Flux initial et liste de flux requis.", code="missing_flows")
        taux = self._resolve_taux(input_)
        flux_initial = valider_montant(input_.base_amount)
        flows = list(input_.flows)
        van = calculer_van_flux(flux_initial, flows, taux)
        ica = round(van / flux_initial, 4) if flux_initial != 0 else 0.0
        return CalculationOutput(
            domain=self.domain,
            sous_theme=self.sous_theme,
            intention=input_.intention or self.intention,
            result=van,
            label="VAN",
            unit=self.unit,
            pedagogical_note=f"VAN = {van} €. ICA = {ica}.",
            extra={"flux_initial": flux_initial, "flows": flows, "van": van, "ica": ica},
        )

    def derive(self, input_: CalculationInput) -> CalculationOutput:
        if input_.base_amount is None or not input_.flows:
            raise CalculationError("Flux initial et liste de flux requis.", code="missing_flows")
        taux = self._resolve_taux(input_)
        flux_initial = valider_montant(input_.base_amount)
        flows = list(input_.flows)
        ica = round(calculer_van_flux(flux_initial, flows, taux) / flux_initial, 4) if flux_initial != 0 else 0.0
        return CalculationOutput(
            domain=self.domain,
            sous_theme=self.sous_theme,
            result=ica,
            label="ICA",
            unit=None,
        )

    def description(self) -> str:
        return (
            "Outil de calcul VAN/ICA : valeur actuelle nette d'une serie de flux "
            "et indice de rentabilite simple."
        )

    def can_handle(self, input_: CalculationInput) -> bool:
        return input_.domain == "finance" and bool(input_.flows) and input_.base_amount is not None

    def _resolve_taux(self, input_: CalculationInput) -> float:
        taux = input_.discount_rate
        if taux is None:
            taux = input_.tau
        if taux is None:
            taux = input_.rate
        if taux is None:
            taux = input_.rate_fraction
        if taux is None:
            raise CalculationError("Un taux d'actualisation est requis.", code="missing_rate")
        return valider_taux(taux)


def register_on(registry: object) -> None:
    """Enregistre le calculateur VAN dans le registre fourni."""
    if hasattr(registry, "register"):
        registry.register(VANChatCalculator)
