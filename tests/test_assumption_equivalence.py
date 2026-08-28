"""Equivalent assumption forms should yield compatible cheap conclusions."""

import pytest
import sympy as sp

from exprtest import is_real, zerotest

x = sp.symbols("x", real=True)


@pytest.mark.parametrize(
    "assumptions",
    [sp.Q.positive(x), x > 0, x >= 1, sp.And(sp.Q.real(x), x > 0)],
)
def test_positive_assumption_forms_prove_cosh_and_log_cases(assumptions):
    assert zerotest(sp.cosh(x), assumptions=assumptions, use_cache=False) is False
    if assumptions != sp.Q.positive(x):
        assert is_real(sp.log(x), assumptions=assumptions) is True


def test_subexpression_assumption_is_used_without_rewriting_symbol_domain():
    y = sp.symbols("y", real=True)
    expr = sp.log(x + y)
    assumptions = sp.Q.positive(x + y)
    assert is_real(expr, assumptions=assumptions) is True


def test_logical_equivalents_produce_same_zero_result():
    expr = sp.log(x) - sp.log(x)
    forms = [sp.Q.positive(x), x > 0, sp.And(sp.Q.real(x), x > 0)]
    assert [zerotest(expr, assumptions=a, use_cache=False) for a in forms] == [
        True,
        True,
        True,
    ]


def test_contradictory_assumptions_remain_inconclusive():
    assumptions = sp.And(x > 0, x < 0)
    assert zerotest(x, assumptions=assumptions, use_cache=False) is None
