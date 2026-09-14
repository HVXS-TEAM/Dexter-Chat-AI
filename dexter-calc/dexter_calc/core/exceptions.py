"""Exceptions metier partagees par tous les modules de calcul de Dexter-Calc."""


class TauxInvalideError(ValueError):
    """Exception levée lorsque le taux est hors de l'intervalle [0, 1]."""

    pass


class MontantInvalideError(ValueError):
    """Exception levée lorsque le montant est négatif."""

    pass


class CalculationError(ValueError):
    """Erreur de calcul métier générique (paramètre ``code`` pour l'API)."""

    def __init__(self, message: str, code: str = "calculation_error"):
        super().__init__(message)
        self.code = code

