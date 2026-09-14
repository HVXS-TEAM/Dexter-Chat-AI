from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.calculator_service import calculator_service

router = APIRouter(prefix="/calculators", tags=["calculators"])


@router.get("/")
def list_calculators(domain: str | None = None, sous_theme: str | None = None):
    """List all available calculators, optionally filtered by domain/sous_theme."""
    calculators = calculator_service.list_calculators()
    if domain:
        calculators = [c for c in calculators if c["domain"] == domain]
    if sous_theme:
        calculators = [c for c in calculators if c.get("sous_theme") == sous_theme]
    return {"count": len(calculators), "calculators": calculators}


@router.get("/{domain}/calculate")
def calculate_get(
    domain: str,
    amount: float | None = None,
    tau: float | None = None,
    rate: float | None = None,
):
    """Simple GET calculation endpoint for quick tests."""
    try:
        result = calculator_service.calculate(domain, {
            "amount": amount,
            "tau": tau,
            "rate": rate,
        })
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{domain}/calculate")
def calculate_post(domain: str, payload: dict[str, Any]):
    """Run a calculation for the given domain with a JSON payload.

    The payload fields are mapped to CalculationInput generics:
    amount_ht, amount_ttc, amount, tau, rate, discount_rate,
    period_years, period_months, periods, flows, base_amount, etc.
    """
    try:
        result = calculator_service.calculate(domain, payload)
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/resolve")
def resolve_and_calculate(payload: dict[str, Any]):
    """Resolve a calculator from the payload and run the calculation.

    Payload must include at least a ``domain`` field.
    """
    domain = payload.get("domain")
    if not domain:
        raise HTTPException(status_code=400, detail="Field 'domain' is required")
    try:
        result = calculator_service.calculate(domain, payload)
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
