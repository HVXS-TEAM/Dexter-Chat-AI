# Dexter-Calc

Un outil pour calculer la TVA et les montants HT/TT.

## Installation

```bash
pip install -e .
```

## Utilisation CLI

### Calculer la TVA collectée
```bash
dexter-calc tva collectee --montant-ht 1000 --taux 0.1925
```

### Calculer la TVA déductible
```bash
dexter-calc tva deductible --montant-ht 1000 --taux 0.1925
```

### Calculer la TVA à payer
```bash
dexter-calc tva payer --tva-collectee 200 --tva-deductible 100
```

### Calculer le montant TTC
```bash
dexter-calc tva ttc --montant-ht 1000 --taux 0.1925
```

### Calculer le montant HT
```bash
dexter-calc tva ht --montant-ttc 1192.50 --taux 0.1925
```

## Utilisation en tant que bibliothèque Python

```python
from dexter_calc.comptabilite.tva import calculer_tva_collectee

result = calculer_tva_collectee(1000, 0.1925)
print(f"TVA collectée: {result:.2f}")
```