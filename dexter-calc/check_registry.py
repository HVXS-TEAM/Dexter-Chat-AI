import os
import sys
# Ensure dexter-calc package root is importable so dexter_calc resolves
root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root)

from dexter_calc.core.calculator import CalculationInput
from dexter_calc.core.registry import CalculatorRegistry
from dexter_calc.finance.van import VANChatCalculator
from dexter_calc.finance.amortissement import AmortissementLineaireCalculator
from dexter_calc.banque.credit_bon import CreditBonCalculator
from dexter_calc.comptabilite.tva import TVACalculator

reg = CalculatorRegistry()
reg.register(TVACalculator)
reg.register(VANChatCalculator)
reg.register(AmortissementLineaireCalculator)
reg.register(CreditBonCalculator)

print("CALCULATORS_OK")
for c in reg.listCalculators():
    print(c)

