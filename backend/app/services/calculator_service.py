from __future__ import annotations

import logging
from typing import Any

from dexter_calc.core.calculator import CalculationInput
from dexter_calc.core.registry import CalculatorRegistry, NoCalculatorFoundError

from app.config import settings

logger = logging.getLogger(__name__)


class CalculatorService:
    def __init__(self) -> None:
        self._registry = CalculatorRegistry()
        self._load_calculators()

    def _load_calculators(self) -> None:
        """Auto-load all available domain calculators into the registry."""
        try:
            from dexter_calc.comptabilite.tva import TVACalculator
            self._registry.register(TVACalculator)
        except Exception as exc:
            logger.warning("Could not load TVACalculator: %s", exc)

        try:
            from dexter_calc.finance.van import VANChatCalculator
            self._registry.register(VANChatCalculator)
        except Exception as exc:
            logger.warning("Could not load VANChatCalculator: %s", exc)

        try:
            from dexter_calc.finance.amortissement import AmortissementLineaireCalculator
            self._registry.register(AmortissementLineaireCalculator)
        except Exception as exc:
            logger.warning("Could not load AmortissementLineaireCalculator: %s", exc)

        try:
            from dexter_calc.banque.credit_bon import CreditBonCalculator
            self._registry.register(CreditBonCalculator)
        except Exception as exc:
            logger.warning("Could not load CreditBonCalculator: %s", exc)

    def list_calculators(self) -> list[dict[str, Any]]:
        return self._registry.list_calculators()

    def get_calculator(self, domain: str | None = None, sous_theme: str | None = None, intention: str | None = None):
        return self._registry.resolve(domain=domain, sous_theme=sous_theme, intention=intention)

    def calculate(self, domain: str, payload: dict[str, Any]) -> dict[str, Any]:
        sous_theme = payload.get("sous_theme")
        calculator = self._registry.resolve(domain=domain, sous_theme=sous_theme)
        input_ = CalculationInput(
            domain=domain,
            sous_theme=payload.get("sous_theme"),
            intention=payload.get("intention"),
            reference_frame=payload.get("reference_frame"),
            profile=payload.get("profile"),
            language=payload.get("language"),
            amount_ht=payload.get("amount_ht"),
            amount_ttc=payload.get("amount_ttc"),
            amount=payload.get("amount"),
            tau=payload.get("tau"),
            rate=payload.get("rate"),
            rate_fraction=payload.get("rate_fraction"),
            period_years=payload.get("period_years"),
            period_months=payload.get("period_months"),
            periods=payload.get("periods"),
            flow=payload.get("flow"),
            flows=payload.get("flows"),
            discount_rate=payload.get("discount_rate"),
            spot_rate=payload.get("spot_rate"),
            forward_rate=payload.get("forward_rate"),
            base_amount=payload.get("base_amount"),
            start_value=payload.get("start_value"),
            comment=payload.get("comment"),
        )
        result = calculator.calc(input_)
        return {
            "domain": result.domain,
            "sous_theme": result.sous_theme,
            "intention": result.intention,
            "reference_frame": result.reference_frame,
            "result": result.result,
            "label": result.label,
            "unit": result.unit,
            "pedagogical_note": result.pedagogical_note,
            "profile": result.profile,
            "language": result.language,
            "display_currency": result.display_currency,
            "extra": result.extra,
        }


calculator_service = CalculatorService()
