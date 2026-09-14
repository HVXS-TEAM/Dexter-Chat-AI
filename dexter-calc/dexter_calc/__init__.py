# Dexter-Calc package initializer.
"""Dexter-Calc: deterministic financial computation helpers."""

from .comptabilite import tva
from .core import (
    CalculationError,
    CalculationInput,
    CalculationOutput,
    CalculatorRegistry,
    DomainCalculator,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "CalculationError",
    "CalculationInput",
    "CalculationOutput",
    "CalculatorRegistry",
    "DomainCalculator",
    "tva",
]
