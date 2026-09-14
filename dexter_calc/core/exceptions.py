class TauxInvalideError(ValueError):
    """Exception levée lorsque le taux de TVA est hors de l'intervalle [0, 1]."""
    pass


class MontantInvalideError(ValueError):
    """Exception levée lorsque le montant est négatif."""
    pass


class CalculationError(ValueError):
    """Erreur de calcul métier (taux invalide, montant invalide, etc.)."""
    pass
