"""Adversarial soundness checks for release validation."""

import pytest
import sympy as sp

from exprtest import profile_zerotest, zerotest


def test_finite_float_literals_use_stored_value():
    assert zerotest(sp.Float("0.0"), use_cache=False) is True
    assert zerotest(sp.Float("1e-11"), use_cache=False) is False


def test_nonfinite_values_never_prove_nonzero():
    for value in (sp.oo, -sp.oo, sp.zoo, sp.nan):
        assert zerotest(value, use_cache=False) is None


def test_branch_sensitive_log_rewrite_is_not_forced():
    z = sp.symbols("z")
    expr = sp.log(z**2, evaluate=False) - 2 * sp.log(z, evaluate=False)
    assert zerotest(expr, use_cache=False, confidence="certified") is None


def test_principal_square_root_identity_is_not_overgeneralized():
    z = sp.symbols("z")
    expr = sp.sqrt(z**2) - z
    assert zerotest(expr, use_cache=False, confidence="certified") is None


def test_dependent_radicals_do_not_create_false_nonzero_proof():
    expr = sp.Add(sp.sqrt(8), -2 * sp.sqrt(2), evaluate=False)
    assert zerotest(expr, use_cache=False) is True


def test_near_zero_exact_algebraic_value_is_not_called_zero():
    n = sp.Integer(10) ** 20
    expr = sp.sqrt(n + 1) - sp.sqrt(n)
    assert zerotest(expr, use_cache=False) is False


def test_known_pole_does_not_become_nonzero_proof():
    expr = sp.gamma(0, evaluate=False)
    assert zerotest(expr, use_cache=False, confidence="certified") is None


def test_inconsistent_assumptions_are_inconclusive():
    x = sp.symbols("x")
    assert zerotest(x, assumptions=sp.false, use_cache=False) is None


def test_mixed_transcendental_combination_is_never_called_zero():
    expr = sp.Add(sp.pi, sp.E, evaluate=False)
    result = zerotest(expr, use_cache=False)
    assert result in (False, None)
    if result is False:
        profile = profile_zerotest(expr)
        assert any(
            stage.stage in {"quick-nonzero", "number-kind", "arb"}
            for stage in profile.stages
        )


def test_symbolic_function_value_is_inconclusive():
    x = sp.symbols("x")
    expr = sp.Function("f")(x)
    assert zerotest(expr, use_cache=False, confidence="certified") is None


def test_float_zero_literals_across_precisions():
    for precision in (1, 4, 11, 20, 53, 100):
        assert zerotest(sp.Float(0, precision), use_cache=False) is True


def test_compound_inexact_cancellation_is_not_an_identity_proof():
    expr = sp.Add(
        sp.Float("0.1"),
        sp.Float("0.2"),
        -sp.Float("0.3"),
        evaluate=False,
    )
    assert zerotest(expr, use_cache=False, confidence="certified") is None


def test_bounded_identity_extensions():
    x = sp.symbols("x", real=True)
    assert zerotest((x**2 - 1) / (x - 1) - (x + 1), use_cache=False) is True
    assert zerotest(sp.Rational(1, 4) ** (-x) - 2 ** (2 * x), use_cache=False) is True
    assert zerotest(sp.sin(2 * x) - 2 * sp.sin(x) * sp.cos(x), use_cache=False) is True


def test_assumption_nonzero_and_definedness():
    x = sp.symbols("x", real=True)
    q = sp.symbols("q")
    assert zerotest(x + 1, assumptions=x > 0, use_cache=False) is False
    assert zerotest(1 / q, assumptions=sp.Eq(q, 0), use_cache=False) is None
    profile = profile_zerotest(1 / q, assumptions=sp.Eq(q, 0))
    assert profile.method == "definedness"


def test_probable_confidence_is_default():
    x = sp.symbols("x")
    expr = sp.sin(x) + 2
    assert zerotest(expr, seed=1, use_cache=False) is False
    assert zerotest(expr, seed=1, use_cache=False, confidence="probable") is False
    assert zerotest(expr, seed=1, use_cache=False, confidence="certified") is None
    with pytest.raises(ValueError):
        zerotest(expr, confidence="guess")
