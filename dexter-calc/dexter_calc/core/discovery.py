"""Discovery helpers for Dexter-Calc domain calculators.

This module provides a function to auto-discover all registered calculators
and return a list of dictionaries describing them.
"""

from __future__ import annotations

from typing import Sequence

from .calculator import DomainCalculator
from .registry import CalculatorRegistry


def discover_calculators(registry: CalculatorRegistry) -> list[dict]:
    """Return a list of dictionaries describing all registered calculators."""
    return registry.listCalculators()
