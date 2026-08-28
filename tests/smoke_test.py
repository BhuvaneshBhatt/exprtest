"""Installed-package smoke test for the public exprtest API."""

from __future__ import annotations

import sympy as sp

import exprtest
from exprtest import ElementOf, Verdict, number_kind, profile_zerotest, zerotest


def main() -> None:
    """Exercise representative public API paths using an installed package."""
    x = sp.symbols("x")
    positive = sp.symbols("positive", positive=True)

    assert exprtest.__version__ != "0+unknown"
    assert zerotest((x + 1) * (x - 1) - x**2 + 1) is True
    assert zerotest(sp.Integer(7)) is False
    assert zerotest(sp.sin(x) + 2) is None
    assert zerotest(positive) is False

    profile = profile_zerotest((x + 1) * (x - 1) - x**2 + 1)
    assert profile.result is True
    assert profile.classification.verdict is Verdict.ZERO_PROVEN
    assert profile.method
    assert profile.reason

    assert exprtest.is_integer(sp.Integer(3)) is True
    assert exprtest.is_rational(sp.Rational(2, 3)) is True
    assert exprtest.is_real(sp.sqrt(2)) is True
    assert exprtest.is_algebraic(sp.sqrt(2)) is True
    assert exprtest.is_prime(sp.Integer(13)) is True
    assert number_kind(sp.Rational(2, 3)).value == "algebraic"
    assert ElementOf(sp.Integer(3), sp.S.Integers) is True

    print(f"exprtest {exprtest.__version__} smoke test passed")


if __name__ == "__main__":
    main()
