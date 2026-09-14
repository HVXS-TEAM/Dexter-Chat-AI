import pytest
from dexter_calc.comptabilite.tva import (
    calculer_tva_collectee,
    calculer_tva_deductible,
    calculer_tva_a_payer,
    calculer_montant_ttc,
    calculer_montant_ht,
)
from dexter_calc.core.exceptions import TauxInvalideError, MontantInvalideError


def test_calculer_tva_collectee():
    assert calculer_tva_collectee(1000, 0.1925) == 192.50


def test_calculer_tva_deductible():
    assert calculer_tva_deductible(1000, 0.1925) == 192.50


def test_calculer_tva_a_payer():
    assert calculer_tva_a_payer(200, 100) == 100
    assert calculer_tva_a_payer(100, 200) == -100


def test_calculer_montant_ttc():
    assert calculer_montant_ttc(1000, 0.1925) == 1192.50


def test_calculer_montant_ht():
    assert calculer_montant_ht(1192.50, 0.1925) == pytest.approx(1000.00)


def test_taux_invalide():
    with pytest.raises(TauxInvalideError):
        calculer_tva_collectee(1000, 1.2)


def test_montant_invalide():
    with pytest.raises(MontantInvalideError):
        calculer_tva_collectee(-1000, 0.1925)