"""Decision 1A (correctif racine) : l'unite et la note pedagogique suivent
``CalculationInput.display_currency``. Sans devise explicite, le defaut
historique « € » est conserve (regle 12 — aucun changement de comportement
pour les appels existants)."""

from dexter_calc.banque.credit_bon import CreditBonCalculator
from dexter_calc.comptabilite.tva import TVACalculator
from dexter_calc.core.calculator import CalculationInput
from dexter_calc.finance.amortissement import AmortissementLineaireCalculator
from dexter_calc.finance.van import VANChatCalculator


def test_credit_unit_and_note_follow_display_currency():
    out = CreditBonCalculator().calc(
        CalculationInput(
            domain="banque",
            base_amount=12000,
            tau=0.05,
            period_months=12,
            display_currency="FCFA",
        )
    )
    assert out.unit == "FCFA"
    assert "600.0 FCFA" in out.pedagogical_note
    assert "€" not in out.pedagogical_note
    assert out.display_currency == "FCFA"


def test_credit_derive_note_follows_display_currency():
    out = CreditBonCalculator().derive(
        CalculationInput(
            domain="banque",
            base_amount=12000,
            tau=0.05,
            period_months=12,
            display_currency="FCFA",
        )
    )
    assert out.unit == "FCFA"
    assert "€" not in out.pedagogical_note
    assert out.display_currency == "FCFA"


def test_tva_unit_follows_display_currency():
    out = TVACalculator().calc(
        CalculationInput(
            domain="comptabilite", amount_ht=1000, tau=0.2, display_currency="XOF"
        )
    )
    assert out.unit == "XOF"
    assert out.display_currency == "XOF"


def test_van_note_follows_display_currency():
    out = VANChatCalculator().calc(
        CalculationInput(
            domain="finance",
            base_amount=10000,
            flows=[3000, 4000, 5000],
            discount_rate=0.1,
            display_currency="FCFA",
        )
    )
    assert out.unit == "FCFA"
    assert "€" not in out.pedagogical_note
    assert out.display_currency == "FCFA"


def test_amortissement_notes_follow_display_currency():
    calc = AmortissementLineaireCalculator()
    for output in (
        calc.calc(
            CalculationInput(
                domain="finance",
                base_amount=12000,
                periods=5,
                period_years=2,
                display_currency="FCFA",
            )
        ),
        calc.derive(
            CalculationInput(
                domain="finance", base_amount=12000, periods=5, display_currency="FCFA"
            )
        ),
    ):
        assert output.unit == "FCFA"
        assert "€" not in output.pedagogical_note
        assert output.display_currency == "FCFA"


def test_default_unit_stays_euro_without_display_currency():
    """Sans devise explicite, le defaut « € » historique est conserve."""
    credit = CreditBonCalculator().calc(
        CalculationInput(domain="banque", base_amount=12000, tau=0.05, period_months=12)
    )
    assert credit.unit == "€"
    assert "€" in credit.pedagogical_note
    assert credit.display_currency == "€"
    tva = TVACalculator().calc(
        CalculationInput(domain="comptabilite", amount_ht=1000, tau=0.2)
    )
    assert tva.unit == "€"
    assert tva.display_currency == "€"
