import typer
from dexter_calc.comptabilite.tva import (
    calculer_tva_collectee,
    calculer_tva_deductible,
    calculer_tva_a_payer,
    calculer_montant_ttc,
    calculer_montant_ht,
)
from dexter_calc.core.calculator import CalculationInput, DomainCalculator
from dexter_calc.core.registry import CalculatorRegistry
from dexter_calc.finance.van import VANChatCalculator
from dexter_calc.finance.amortissement import AmortissementLineaireCalculator
from dexter_calc.banque.credit_bon import CreditBonCalculator

app = typer.Typer()


def _enregistrer_calculators(registry: CalculatorRegistry) -> CalculatorRegistry:
    registry.register(VANChatCalculator)
    registry.register(AmortissementLineaireCalculator)
    registry.register(CreditBonCalculator)
    return registry


@app.command()
def collectee(montant_ht: float, taux: float):
    """Calcule la TVA collectée."""
    try:
        result = calculer_tva_collectee(montant_ht, taux)
        typer.echo(f"TVA collectée: {result:.2f}")
    except Exception as e:
        typer.echo(f"Erreur: {str(e)}", err=True)


@app.command()
def deductible(montant_ht: float, taux: float):
    """Calcule la TVA déductible."""
    try:
        result = calculer_tva_deductible(montant_ht, taux)
        typer.echo(f"TVA déductible: {result:.2f}")
    except Exception as e:
        typer.echo(f"Erreur: {str(e)}", err=True)


@app.command()
def payer(tva_collectee: float, tva_deductible: float):
    """Calcule la TVA à payer ou le crédit de TVA."""
    try:
        result = calculer_tva_a_payer(tva_collectee, tva_deductible)
        if result >= 0:
            typer.echo(f"TVA à payer: {result:.2f}")
        else:
            typer.echo(f"Crédit de TVA: {abs(result):.2f}")
    except Exception as e:
        typer.echo(f"Erreur: {str(e)}", err=True)


@app.command()
def ttc(montant_ht: float, taux: float):
    """Calcule le montant TTC."""
    try:
        result = calculer_montant_ttc(montant_ht, taux)
        typer.echo(f"Montant TTC: {result:.2f}")
    except Exception as e:
        typer.echo(f"Erreur: {str(e)}", err=True)


@app.command()
def ht(montant_ttc: float, taux: float):
    """Calcule le montant HT."""
    try:
        result = calculer_montant_ht(montant_ttc, taux)
        typer.echo(f"Montant HT: {result:.2f}")
    except Exception as e:
        typer.echo(f"Erreur: {str(e)}", err=True)


if __name__ == "__main__":
    app()