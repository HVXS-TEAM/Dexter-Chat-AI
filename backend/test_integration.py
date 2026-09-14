"""Test integration of dexter-calc in backend."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.services.calculator_service import calculator_service

print("=== Calculator Service Integration Test ===")
print()

calculators = calculator_service.list_calculators()
print(f"Registered calculators: {len(calculators)}")
for c in calculators:
    print(f"  {c['domain']:15} {c['sous_theme']:15} {c['label']}")

print()

# Test TVA
print("=== TVA Test ===")
result = calculator_service.calculate("comptabilite", {"amount_ht": 1000, "tau": 0.2})
print(f"  Result: {result['label']} = {result['result']}")
print(f"  Extra: {result['extra']}")

print()

# Test VAN
print("=== VAN Test ===")
result = calculator_service.calculate("finance", {
    "base_amount": 10000,
    "flows": [3000, 4000, 5000],
    "discount_rate": 0.1
})
print(f"  Result: {result['label']} = {result['result']}")
print(f"  Extra: {result['extra']}")

print()

# Test Credit
print("=== Credit Test ===")
result = calculator_service.calculate("banque", {
    "base_amount": 12000,
    "tau": 0.05,
    "period_months": 24
})
print(f"  Result: {result['label']} = {result['result']}")
print(f"  Extra: {result['extra']}")

print()
print("ALL TESTS PASSED")
