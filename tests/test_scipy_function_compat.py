"""Optional regression checks for the SciPy counterparts documented by exprtest."""

import csv
from pathlib import Path

import pytest
import sympy as sp

pytestmark = pytest.mark.scipy_compat


def _special():
    return pytest.importorskip("scipy.special")


def _as_complex(value):
    return complex(sp.N(value, 16))


@pytest.mark.parametrize("x", [-1.25, 0.0, 0.75, 0.5 + 0.75j])
def test_scipy_erf_matches_sympy_definition(x):
    special = _special()
    assert special.erf(x) == pytest.approx(
        _as_complex(sp.erf(sp.sympify(x))), rel=1e-13, abs=1e-13
    )


@pytest.mark.parametrize("x", [-1.25, 0.0, 0.75, 0.5 + 0.75j])
def test_scipy_erfc_matches_sympy_definition(x):
    special = _special()
    assert special.erfc(x) == pytest.approx(
        _as_complex(sp.erfc(sp.sympify(x))), rel=1e-13, abs=1e-13
    )


def test_gamma_is_not_advertised_as_exact_library_behavior_equivalent():
    special = _special()
    assert special.gamma(-1.0) != special.gamma(-1.0)  # IEEE NaN in modern SciPy
    assert sp.gamma(-1) is sp.zoo


def test_loggamma_is_not_advertised_as_exact_real_dtype_equivalent():
    special = _special()
    assert special.loggamma(-0.5) != special.loggamma(-0.5)  # real dtype returns NaN
    assert sp.loggamma(sp.Rational(-1, 2)).evalf().is_finite is True


def test_inventory_advertises_only_verified_scipy_counterparts():
    path = Path(__file__).parents[1] / "docs" / "function_facts.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    mapped = {
        row["sympy"]: row["scipy_equivalent"] for row in rows if row["scipy_equivalent"]
    }
    assert mapped == {
        "erf": "scipy.special.erf",
        "erfc": "scipy.special.erfc",
    }
