"""Test complet du package dexter-calc."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dexter-calc'))

from dexter_calc.finance.van import VANChatCalculator
from dexter_calc.finance.amortissement import AmortissementLineaireCalculator
from dexter_calc.banque.credit_bon import CreditBonCalculator
from dexter_calc.comptabilite.tva import TVACalculator
from dexter_calc.core.registry import CalculatorRegistry
from dexter_calc.core.calculator import CalculationInput

reg = CalculatorRegistry()
reg.register(TVACalculator)
reg.register(VANChatCalculator)
reg.register(AmortissementLineaireCalculator)
reg.register(CreditBonCalculator)

print('=== DEXTER-CALC MODULES ===')
for c in reg.listCalculators():
    print(f"  {c['domain']:15} {c['sous_theme']:15} {c['label']}")

print()
print('=== TEST TVA ===')
tva = TVACalculator()
r = tva.calc(CalculationInput(domain='comptabilite', amount_ht=1000, tau=0.2))
print(f"  Montant HT: 1000 EUR, Taux: 20%")
print(f"  TVA collectee: {r.extra['tva_collectee']} EUR")
print(f"  Montant TTC: {r.extra['montant_ttc']} EUR")

print()
print('=== TEST VAN ===')
van = VANChatCalculator()
r = van.calc(CalculationInput(domain='finance', base_amount=10000, flows=[3000, 4000, 5000], discount_rate=0.1))
print(f"  Investissement: 10000 EUR, Flux: [3000, 4000, 5000], Taux: 10%")
print(f"  VAN: {r.extra['van']} EUR")
print(f"  ICA: {r.extra['ica']}")

print()
print('=== TEST CREDIT BANCAIRE ===')
credit = CreditBonCalculator()
r = credit.calc(CalculationInput(domain='banque', base_amount=12000, tau=0.05, period_months=24))
print(f"  Capital: 12000 EUR, Taux: 5%, Duree: 24 mois")
print(f"  Interet simple: {r.extra['interet_simple']} EUR")
print(f"  Capital final: {r.extra['capital_final']} EUR")
print(f"  Mensualite simplifiee: {r.extra['mensualite_simple']} EUR/mois")

print()
print('=== TEST AMORTISSEMENT LINEAIRE ===')
amort = AmortissementLineaireCalculator()
r = amort.calc(CalculationInput(domain='finance', base_amount=12000, periods=5, period_years=2))
print(f"  Valeur: 12000 EUR, Duree: 5 ans, Annees ecoulees: 2")
print(f"  Dotation annuelle: {r.extra['dotation_annuelle']} EUR")
print(f"  Valeur residuelle: {r.extra['valeur_reesiduelle']} EUR")

print()
print('ALL TESTS PASSED')
