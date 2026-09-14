"""Registry of domain calculators for Dexter-Calc.

Each domain module registers its calculator classes here so that Dexter
can discover tools by domain, sous_theme and intention without hardcoding
the catalogue in Dexter itself.
"""

from __future__ import annotations

from typing import Any

from .calculator import CalculationInput, CalculationOutput, DomainCalculator


class NoCalculatorFoundError(ValueError):
    """Raised when no calculator matches a given request."""

    pass


class CalculatorRegistry:
    """Light registry for Dexter-Calc tools.

    Calculators are registered by domain and optional sous_theme and
    intention. Discovery is done through lookup methods instead of a
    monolithic switch.
    """

    def __init__(self) -> None:
        self._catalog: dict[str, list[DomainCalculator]] = {}

    def register(self, calculator: type[DomainCalculator]) -> type[DomainCalculator]:
        instance = calculator()
        key = instance.domain or calculator.__name__
        self._catalog.setdefault(key, []).append(instance)
        return calculator

    def get_calculators(self, domain: str) -> list[DomainCalculator]:
        return self._catalog.get(domain, [])

    def find(
        self,
        domain: str | None = None,
        sous_theme: str | None = None,
        intention: str | None = None,
    ) -> list[DomainCalculator]:
        candidates: list[DomainCalculator] = []
        for instances in self._catalog.values():
            for calc in instances:
                if domain and calc.domain != domain:
                    continue
                if sous_theme and calc.sous_theme != sous_theme:
                    continue
                if intention and calc.intention not in (intention, "*",):
                    continue
                candidates.append(calc)
        return candidates

    def resolve(
        self,
        domain: str | None = None,
        sous_theme: str | None = None,
        intention: str | None = None,
    ) -> DomainCalculator:
        matches = self.find(domain=domain, sous_theme=sous_theme, intention=intention)
        if not matches:
            raise NoCalculatorFoundError(
                f"No calculator found for domain={domain}, sous_theme={sous_theme}, intention={intention}"
            )
        return matches[0]

    def list_calculators(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for domain, instances in sorted(self._catalog.items()):
            for calc in instances:
                result.append({
                    "domain": calc.domain,
                    "sous_theme": calc.sous_theme,
                    "intention": calc.intention,
                    "label": calc.label,
                    "unit": calc.unit,
                })
        return result
