"""Validation helpers shared by all Dexter-Calc computation modules."""

import math
from typing import Union

from .exceptions import MontantInvalideError, TauxInvalideError

Nombre = Union[int, float]


def _rejeter_booleen(valeur: object, erreur: type[ValueError], message: str) -> None:
    """Reject booleans explicitly (bool is a subclass of int in Python)."""
    if isinstance(valeur, bool):
        raise erreur(message)


def valider_montant(montant: Nombre) -> float:
    """Validate that an amount is a finite number >= 0. Return it as float."""
    _rejeter_booleen(montant, MontantInvalideError, "Le montant doit etre un nombre.")
    if not isinstance(montant, (int, float)):
        raise MontantInvalideError("Le montant doit etre un nombre.")
    valeur = float(montant)
    if math.isnan(valeur) or math.isinf(valeur):
        raise MontantInvalideError("Le montant doit etre un nombre fini.")
    if valeur < 0:
        raise MontantInvalideError("Le montant ne peut pas etre negatif.")
    return valeur


def valider_taux(taux: Nombre) -> float:
    """Validate that a rate is a finite number in [0, 1]. Return it as float."""
    _rejeter_booleen(taux, TauxInvalideError, "Le taux doit etre un nombre.")
    if not isinstance(taux, (int, float)):
        raise TauxInvalideError("Le taux doit etre un nombre.")
    valeur = float(taux)
    if math.isnan(valeur) or math.isinf(valeur):
        raise TauxInvalideError("Le taux doit etre un nombre fini.")
    if valeur < 0 or valeur > 1:
        raise TauxInvalideError("Le taux doit etre compris entre 0 et 1.")
    return valeur
