"""Regression cases adapted from historical symbolic zero-test suites.

The cases here keep only expressions that map cleanly to SymPy and exercise
``zerotest`` directly.  Frontend-specific message checks, timing wrappers,
special-function examples, and duplicated cases are intentionally omitted.
"""

import pytest
import sympy as sp

from exprtest import zerotest

x, y, c, d, r, n, v, a = sp.symbols("x y c d r n v a")


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        (
            sp.sqrt(2) + sp.sqrt(3) - sp.sqrt(5 + 2 * sp.sqrt(6)),
            True,
        ),
        (
            2 * sp.log(sp.sqrt(2) + sp.sqrt(3)) - sp.log(5 + 2 * sp.sqrt(6)),
            True,
        ),
        (-1 + sp.exp(sp.E ** (-(sp.E**6))), False),
        (sp.exp(sp.I * sp.pi / 4) - (-1) ** sp.Rational(1, 4), True),
        ((sp.E + sp.pi) ** 2 - sp.E**2 - sp.pi**2 - 2 * sp.E * sp.pi, True),
        (sp.exp(sp.pi) - sp.pi**sp.E, False),
        (2 * sp.log(5) - sp.log(25), True),
        (sp.sqrt((-2) ** sp.I) - (-2) ** (sp.I / 2), True),
        (sp.exp(sp.I * sp.pi + x) + sp.exp(x), True),
        (
            sp.Integer(245416245445421954452459541)
            - 3
            * sp.sqrt(sp.Integer(6692125947614176911440676402530490513423056191461390)),
            False,
        ),
        (-sp.exp(sp.Rational(62795307, 45297239)), False),
        ((sp.pi + 8 * sp.atan(1 - sp.sqrt(2))) / (8 * sp.pi), True),
        (
            sp.Integer(34967586868203284666575423396341074438)
            - sp.Integer(21208913531730155539833556128356679037) * sp.sqrt(sp.E),
            False,
        ),
        (sp.cos(4 * sp.pi / 59), False),
        (sp.GoldenRatio - 1 / sp.GoldenRatio - 1, True),
        (
            sp.GoldenRatio - 1 / sp.GoldenRatio - 1 + sp.Rational(1, 10**100),
            False,
        ),
        (sp.tan(sp.tan(sp.tan(sp.E))), False),
        (-1 + (-1) ** sp.Rational(1, 3) - (-1) ** sp.Rational(2, 3), True),
    ],
)
def test_closed_expression_regressions(expr, expected):
    assert zerotest(expr, use_cache=False) is expected


def test_hidden_zero_perturbed_by_tiny_exact_nonzero_term():
    zero = 2 * sp.log(sp.sqrt(2) + sp.sqrt(3)) - sp.log(5 + 2 * sp.sqrt(6))
    # This is mathematically nonzero, but the current bounded oracle does not
    # yet separate this transcendental perturbation reliably.
    assert zerotest(zero + sp.exp(-1000), use_cache=False) is None


def test_finite_float_literals_are_classified_by_stored_value():
    assert zerotest(sp.Float("0.0"), use_cache=False) is True
    assert zerotest(sp.Float("-0.0"), use_cache=False) is True
    assert zerotest(sp.Float("1e-11"), use_cache=False) is False


@pytest.mark.parametrize("prec", [1, 4, 11, 20, 53, 100])
def test_float_zero_is_zero_at_any_precision(prec):
    # SymPy floating values carry precision metadata directly. Every finite
    # representation of literal zero
    # is nevertheless exactly the floating value zero.
    assert zerotest(sp.Float(0, prec), use_cache=False) is True


def test_principal_square_root_is_not_identity_without_assumptions():
    expr = sp.sqrt(x**2) - x
    assert zerotest(expr, use_cache=False, confidence="certified") is None


def test_principal_square_root_with_positive_symbol():
    xp = sp.Symbol("xp", positive=True)
    assert zerotest(sp.sqrt(xp**2) - xp, use_cache=False) is True


@pytest.mark.parametrize(
    "expr",
    [
        12
        - (c + (-c - d + sp.sqrt(48 + c**2 - 2 * c * d + d**2)) / 2)
        * (d + (-c - d + sp.sqrt(48 + c**2 - 2 * c * d + d**2)) / 2),
    ],
)
def test_known_identity_cases_not_falsely_called_nonzero(expr):
    # These historical cases identify useful completeness targets.  Until the
    # bounded identity machinery handles them, returning None is preferable to
    # a false nonzero result.
    assert zerotest(expr, use_cache=False) in (True, None)


@pytest.mark.parametrize(
    "expr",
    [
        (x + 1) * (x - 1) - x**2 + 1,
        1 / x + 1 / y - (x + y) / (x * y),
        -sp.E + sp.exp(1 / (1 + r) + r / (1 + r)),
        sp.Rational(1, 2) ** (-n) - 2**n,
        -(sp.I**v) + sp.exp(sp.I * sp.pi * v / 2),
        sp.log(3**sp.pi) - sp.pi * sp.log(3),
        2 ** (2 * a) / 4**a - 1,
        2 * sp.cos(1) * sp.sin(1) - sp.sin(2),
        sp.sin(sp.pi / 2 + x) - sp.cos(x),
    ],
)
def test_bounded_identity_normalizers_prove_common_identities(expr):
    assert zerotest(expr, use_cache=False) is True


def test_rational_cancellation_with_transcendental_subexpression():
    t = sp.sin(sp.log(140))
    expr = (
        140
        + sp.pi
        + (140 + sp.pi) * (-sp.Rational(990, 7) + t) / (sp.Rational(990, 7) - t)
    )
    assert zerotest(expr, use_cache=False) in (True, None)


def test_profile_reports_bounded_identity_decision():
    from exprtest import profile_zerotest

    profile = profile_zerotest((x + 1) * (x - 1) - x**2 + 1)
    assert profile.result is True
    assert profile.method == "elementary-identity"
    assert "identity" in profile.reason.lower()


def test_large_power_is_not_expanded_by_rational_identity_layer():
    from exprtest._identity import rational_identity_normal_form

    expr = (x + 1) ** 10000 - (x + 3) ** 10000
    assert rational_identity_normal_form(expr) == expr


def test_exact_exp_log_extensions():
    z = sp.symbols("z")
    n = sp.symbols("n", integer=True)
    periodic = sp.Add(
        sp.exp(z + 2 * sp.pi * sp.I * n, evaluate=False),
        -sp.exp(z, evaluate=False),
        evaluate=False,
    )
    assert zerotest(periodic, use_cache=False) is True

    positive = sp.symbols("positive", positive=True)
    expr = sp.exp(2 * sp.log(positive)) - positive**2
    assert zerotest(expr, use_cache=False) is True
