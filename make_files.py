import os, pathlib

base = pathlib.Path("e:/Projets Edwin/New/Chatbot & Calco/Dexter Chat AI/dexter-calc")
for d in ["dexter_calc/finance", "dexter_calc/banque"]:
    pp = base / d
    pp.mkdir(parents=True, exist_ok=True)
    (pp / "__init__.py").write_text("# martial package\n")
    print("created", pp)

for name, body in [
    ("dexter_calc/core/exceptions.py", "class TauxInvalideError(ValueError):\n    '''Exception leve lorsque le taux de TVA est hors de l'intervalle [0, 1].'''\n    pass\n\n\nclass MontantInvalideError(ValueError):\n    '''Exception leve lorsque le montant est negatif.'''\n    pass\n\n\nclass CalculationError(ValueError):\n    '''Erreur de calcul metier (taux invalide, montant invalide, etc.).'''\n    pass\n"),
    ("dexter_calc/core/__init__.py", "from .calculator import CalculationInput, CalculationOutput, DomainCalculator\nfrom .exceptions import CalculationError\nfrom .registry import CalculatorRegistry\n\n__all__ = [\n    'CalculationInput',\n    'CalculationOutput',\n    'DomainCalculator',\n    'CalculationError',\n    'CalculatorRegistry',\n]\n"),
]:
    p = base / name
    p.write_text(body)
    print("wrote", p)
