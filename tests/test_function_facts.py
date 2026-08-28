"""Regression coverage for every retained SymPy function fact."""

import csv
from pathlib import Path

import pytest
import sympy as sp

from exprtest import is_integer, is_real, zerotest
from exprtest._defined import quick_defined
from exprtest._function_facts import PROPERTY_FUNCS, function_defined, function_property

x = sp.symbols("x", real=True)
n = sp.symbols("n", integer=True)
nn = sp.symbols("nn", integer=True, nonnegative=True)
np = sp.symbols("np", integer=True, positive=True)
z = sp.symbols("z")


def _closed(func, arg):
    return func(arg, evaluate=False)


# One applicability witness for every documented non-domain fact.  The concrete
# witness independently checks the same property through SymPy's own evaluated
# expression/assumption machinery where that machinery exposes it.
PROPERTY_CASES = [
    # Abs
    ("Abs", sp.Abs(x), "integer", sp.Q.integer(x), sp.Abs(-3)),
    ("Abs", sp.Abs(z), "real", True, sp.Abs(1 + sp.I)),
    ("Abs", sp.Abs(x), "positive", sp.Q.nonzero(x), sp.Abs(-2)),
    ("Abs", sp.Abs(z), "nonnegative", True, sp.Abs(0)),
    # acos
    ("acos", sp.acos(x), "real", sp.And(x >= -1, x <= 1), sp.acos(0)),
    ("acos", sp.acos(x), "positive", sp.And(x >= -1, x < 1), sp.acos(0)),
    ("acos", sp.acos(x), "nonnegative", sp.And(x >= -1, x <= 1), sp.acos(1)),
    # asin
    ("asin", sp.asin(x), "real", sp.And(x >= -1, x <= 1), sp.asin(0)),
    ("asin", sp.asin(x), "positive", sp.And(x > 0, x <= 1), sp.asin(sp.Rational(1, 2))),
    (
        "asin",
        sp.asin(x),
        "negative",
        sp.And(x >= -1, x < 0),
        sp.asin(sp.Rational(-1, 2)),
    ),
    ("asin", sp.asin(x), "nonnegative", sp.And(x >= 0, x <= 1), sp.asin(0)),
    ("asin", sp.asin(x), "nonpositive", sp.And(x >= -1, x <= 0), sp.asin(0)),
    # atan
    ("atan", sp.atan(x), "real", True, sp.atan(1)),
    ("atan", sp.atan(x), "positive", x > 0, sp.atan(1)),
    ("atan", sp.atan(x), "negative", x < 0, sp.atan(-1)),
    ("atan", sp.atan(x), "nonnegative", x >= 0, sp.atan(0)),
    ("atan", sp.atan(x), "nonpositive", x <= 0, sp.atan(0)),
    # ceiling
    ("ceiling", sp.ceiling(x), "integer", True, sp.ceiling(sp.Rational(1, 2))),
    ("ceiling", sp.ceiling(x), "real", True, sp.ceiling(sp.Rational(1, 2))),
    ("ceiling", sp.ceiling(x), "positive", x > 0, sp.ceiling(sp.Rational(1, 2))),
    ("ceiling", sp.ceiling(x), "negative", x <= -1, sp.ceiling(sp.Rational(-3, 2))),
    ("ceiling", sp.ceiling(x), "nonnegative", x > -1, sp.ceiling(sp.Rational(-1, 2))),
    ("ceiling", sp.ceiling(x), "nonpositive", x <= 0, sp.ceiling(0)),
    # cos
    ("cos", sp.cos(x), "real", True, sp.cos(1)),
    # cosh
    ("cosh", sp.cosh(x), "real", True, sp.cosh(0)),
    ("cosh", sp.cosh(x), "positive", True, sp.cosh(0)),
    ("cosh", sp.cosh(x), "nonnegative", True, sp.cosh(0)),
    # erf
    ("erf", sp.erf(x), "real", True, sp.erf(1)),
    ("erf", sp.erf(x), "positive", x > 0, sp.erf(1)),
    ("erf", sp.erf(x), "negative", x < 0, sp.erf(-1)),
    ("erf", sp.erf(x), "nonnegative", x >= 0, sp.erf(0)),
    ("erf", sp.erf(x), "nonpositive", x <= 0, sp.erf(0)),
    # erfc
    ("erfc", sp.erfc(x), "real", True, sp.erfc(0)),
    ("erfc", sp.erfc(x), "positive", True, sp.erfc(0)),
    ("erfc", sp.erfc(x), "nonnegative", True, sp.erfc(0)),
    # factorial
    ("factorial", sp.factorial(nn), "integer", True, sp.factorial(3)),
    ("factorial", sp.factorial(x), "real", x > -1, sp.factorial(sp.Rational(1, 2))),
    ("factorial", sp.factorial(x), "positive", x > -1, sp.factorial(0)),
    ("factorial", sp.factorial(x), "nonnegative", x > -1, sp.factorial(0)),
    # floor
    ("floor", sp.floor(x), "integer", True, sp.floor(sp.Rational(1, 2))),
    ("floor", sp.floor(x), "real", True, sp.floor(sp.Rational(1, 2))),
    ("floor", sp.floor(x), "positive", x >= 1, sp.floor(1)),
    ("floor", sp.floor(x), "negative", x < 0, sp.floor(sp.Rational(-1, 2))),
    ("floor", sp.floor(x), "nonnegative", x >= 0, sp.floor(0)),
    ("floor", sp.floor(x), "nonpositive", x < 1, sp.floor(sp.Rational(1, 2))),
    # gamma
    ("gamma", sp.gamma(np), "integer", True, sp.gamma(3)),
    (
        "gamma",
        _closed(sp.gamma, sp.Rational(-1, 2)),
        "real",
        True,
        sp.gamma(sp.Rational(-1, 2)),
    ),
    ("gamma", sp.gamma(x), "positive", x > 0, sp.gamma(1)),
    ("gamma", sp.gamma(x), "nonnegative", x > 0, sp.gamma(1)),
    # log
    ("log", sp.log(x), "real", x > 0, sp.log(2)),
    ("log", sp.log(x), "positive", x > 1, sp.log(2)),
    ("log", sp.log(x), "negative", sp.And(x > 0, x < 1), sp.log(sp.Rational(1, 2))),
    ("log", sp.log(x), "nonnegative", x >= 1, sp.log(1)),
    ("log", sp.log(x), "nonpositive", sp.And(x > 0, x <= 1), sp.log(1)),
    # loggamma
    ("loggamma", sp.loggamma(x), "real", x > 0, sp.loggamma(1)),
    (
        "loggamma",
        sp.loggamma(x),
        "positive",
        sp.And(x > 0, x < 1),
        sp.loggamma(sp.Rational(1, 2)),
    ),
    (
        "loggamma",
        sp.loggamma(x),
        "negative",
        sp.And(x > 1, x < 2),
        sp.loggamma(sp.Rational(3, 2)),
    ),
    ("loggamma", sp.loggamma(x), "nonnegative", sp.And(x > 0, x <= 1), sp.loggamma(1)),
    ("loggamma", sp.loggamma(x), "nonpositive", sp.And(x >= 1, x <= 2), sp.loggamma(1)),
    # sin / sinh
    ("sin", sp.sin(x), "real", True, sp.sin(1)),
    ("sinh", sp.sinh(x), "real", True, sp.sinh(1)),
    # tanh
    ("tanh", sp.tanh(x), "real", True, sp.tanh(1)),
    ("tanh", sp.tanh(x), "positive", x > 0, sp.tanh(1)),
    ("tanh", sp.tanh(x), "negative", x < 0, sp.tanh(-1)),
    ("tanh", sp.tanh(x), "nonnegative", x >= 0, sp.tanh(0)),
    ("tanh", sp.tanh(x), "nonpositive", x <= 0, sp.tanh(0)),
    # zeta
    ("zeta", sp.zeta(x), "real", x > 1, sp.zeta(2)),
    ("zeta", sp.zeta(x), "positive", x > 1, sp.zeta(2)),
    ("zeta", sp.zeta(x), "negative", sp.And(x > -2, x < 1), sp.zeta(0)),
    ("zeta", sp.zeta(x), "nonnegative", x > 1, sp.zeta(2)),
    ("zeta", sp.zeta(x), "nonpositive", sp.And(x >= -2, x < 1), sp.zeta(-2)),
]


# Every documented definedness rule has a finite witness.  For functions with a
# genuine discrete singular set, the second table locks down the excluded point.
DEFINED_CASES = [
    ("Abs", sp.Abs(z)),
    ("acos", sp.acos(z)),
    ("asin", sp.asin(z)),
    ("atan", _closed(sp.atan, 0)),
    ("cos", sp.cos(z)),
    ("cosh", sp.cosh(z)),
    ("erf", sp.erf(z)),
    ("erfc", sp.erfc(z)),
    ("factorial", _closed(sp.factorial, sp.Rational(-1, 2))),
    ("gamma", _closed(sp.gamma, sp.Rational(-1, 2))),
    ("log", _closed(sp.log, 2)),
    ("loggamma", _closed(sp.loggamma, sp.Rational(-1, 2))),
    ("sin", sp.sin(z)),
    ("sinc", sp.sinc(z)),
    ("sinh", sp.sinh(z)),
    ("tan", _closed(sp.tan, 0)),
    ("tanh", _closed(sp.tanh, 0)),
    ("zeta", _closed(sp.zeta, 2)),
]

UNDEFINED_CASES = [
    _closed(sp.atan, sp.I),
    _closed(sp.tan, sp.pi / 2),
    _closed(sp.tanh, sp.I * sp.pi / 2),
    _closed(sp.gamma, 0),
    _closed(sp.factorial, -1),
    _closed(sp.log, 0),
    _closed(sp.loggamma, 0),
    _closed(sp.zeta, 1),
]


@pytest.mark.parametrize("name,term,prop,assumptions,concrete", PROPERTY_CASES)
def test_every_retained_property_has_a_regression(
    name, term, prop, assumptions, concrete
):
    assert term.func.__name__ == name
    assert function_property(term, prop, assumptions) is True
    sympy_prop = getattr(concrete, f"is_{prop}")
    if sympy_prop is not None:
        assert sympy_prop is True


@pytest.mark.parametrize("name,term", DEFINED_CASES)
def test_every_retained_domain_fact_has_a_regression(name, term):
    assert term.func.__name__ == name
    assert function_defined(term) is True


@pytest.mark.parametrize("term", UNDEFINED_CASES)
def test_discrete_singularities_are_rejected(term):
    assert function_defined(term) is False
    assert quick_defined(term) is False


def test_principal_branch_cuts_are_not_misclassified_as_poles():
    # SymPy has finite principal values at these cut points; only the actual
    # singular points are excluded by the registry.
    assert function_defined(_closed(sp.log, -1)) is True
    assert function_defined(_closed(sp.atan, 2 * sp.I)) is True
    assert function_defined(_closed(sp.loggamma, sp.Rational(-1, 2))) is True


def test_factorial_extension_matches_sympy_gamma_rewrite():
    value = _closed(sp.factorial, sp.Rational(-1, 2))
    assert function_defined(value) is True
    assert value.rewrite(sp.gamma) == sp.sqrt(sp.pi)
    assert function_property(value, "real") is True


@pytest.mark.parametrize(
    "term,prop",
    [
        (_closed(sp.Abs, sp.I), "integer"),
        (_closed(sp.cos, sp.I), "real"),
        (_closed(sp.cosh, sp.I), "positive"),
        (_closed(sp.gamma, sp.Rational(-7, 2)), "positive"),
        (_closed(sp.factorial, sp.Rational(-5, 2)), "positive"),
        (_closed(sp.zeta, sp.Rational(-7, 2)), "positive"),
    ],
)
def test_sufficient_conditions_never_become_false_property_proofs(term, prop):
    assert function_property(term, prop) is not False


def test_floor_and_ceiling_rules_are_real_input_rules_only():
    assert function_property(sp.floor(x), "integer") is True
    assert function_property(sp.ceiling(x), "integer") is True
    # SymPy generalizes these functions componentwise to complex arguments, so
    # a complex result is not claimed to be an ordinary integer or real value.
    assert function_property(sp.floor(z), "integer") is None
    assert function_property(sp.ceiling(z), "real") is None


def test_function_facts_feed_public_zero_and_domain_apis():
    assert zerotest(sp.cosh(x), assumptions=sp.Q.real(x), use_cache=False) is False
    assert zerotest(sp.erfc(x), assumptions=sp.Q.real(x), use_cache=False) is False
    assert zerotest(sp.erf(x), assumptions=x > 0, use_cache=False) is False
    assert zerotest(sp.zeta(x), assumptions=x > 1, use_cache=False) is False
    assert zerotest(sp.log(x), assumptions=x > 1, use_cache=False) is False
    assert (
        zerotest(sp.asin(x), assumptions=sp.And(x > 0, x <= 1), use_cache=False)
        is False
    )
    assert is_real(sp.acos(x), assumptions=sp.And(x >= -1, x <= 1)) is True
    assert is_integer(sp.floor(x), assumptions=sp.Q.real(x)) is True
    assert is_integer(sp.ceiling(x), assumptions=sp.Q.real(x)) is True


def _inventory_rows():
    path = Path(__file__).parents[1] / "docs" / "function_facts.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_every_documented_property_is_covered_by_the_regression_table():
    documented = set()
    for row in _inventory_rows():
        for prop in row["properties"].split(";"):
            if prop != "defined":
                documented.add((row["sympy"], prop))
    covered = {(name, prop) for name, _, prop, _, _ in PROPERTY_CASES}
    assert covered == documented


def test_every_documented_domain_fact_is_covered_by_the_regression_table():
    documented = {
        row["sympy"]
        for row in _inventory_rows()
        if "defined" in row["properties"].split(";")
    }
    covered = {name for name, _ in DEFINED_CASES}
    assert covered == documented


def test_committed_function_inventory_matches_runtime_registry():
    rows = _inventory_rows()
    documented = {row["sympy"] for row in rows}
    runtime = {func.__name__ for func in PROPERTY_FUNCS}
    assert documented == runtime
