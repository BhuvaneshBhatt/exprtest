"""Compatibility imports for the expression predicates now in exprtools."""

from importlib.metadata import PackageNotFoundError, version
from exprtools import (
    ElementOf,
    Verdict,
    ZeroClassification,
    is_algebraic,
    is_integer,
    is_prime,
    is_rational,
    is_real,
    number_kind,
    profile_zerotest,
    zerotest,
)

__all__ = [
    "ElementOf",
    "Verdict",
    "ZeroClassification",
    "is_algebraic",
    "is_integer",
    "is_prime",
    "is_rational",
    "is_real",
    "number_kind",
    "profile_zerotest",
    "zerotest",
]
try:
    __version__ = version("exprtest")
except PackageNotFoundError:
    __version__ = "0+unknown"
