"""Write a clean credit_bon.py module."""
content += r'''

class CreditBonCalculator(DomainCalculator):
    """Calculateur d'interet simple et de remboursement pour le credit bancaire.

    Domaines couverts : banque / gestion financiere personnelle / credit a la
    consommation. Outil pedagogique pour comprendre le cout d'un emprunt.
    """

    domain: str = "banque"
    sous_theme: str | None = "credit"
    intention: str | None = "calcul"
    reference_frame: str | None = None
    label: str = "Calcul du cout d'emprunt (banque)"
    unit: str | None = "€"

    supported_intentions: tuple[str, ...] = ("calcul", "explique_moi", "pourquoi")
    supported_profiles: tuple[str, ...] = ("etudiant", "professeur")
'''
with open("credit_bon.py", "a", encoding="utf-8") as f:
    f.write(content)
print("Part 2 written")

