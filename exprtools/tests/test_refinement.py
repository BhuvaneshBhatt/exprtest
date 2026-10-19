"""Positive and adversarial branch/domain checks for the independent engine."""

import importlib

import pytest
import sympy as s
from sympy.assumptions import assuming

from exprtools import SimplificationBudget, refine

B = SimplificationBudget(seconds=5, max_steps=100)
x, z = s.symbols("x z")


@pytest.mark.parametrize(
    "assumption,expected",
    [
        (s.Q.positive(x), x),
        (x > 0, x),
        (s.Q.negative(x), -x),
        (x <= 0, -x),
        (s.Eq(x, 0), s.S.Zero),
        (True, s.Abs(x)),
    ],
)
def test_absolute_value(assumption, expected):
    assert refine(s.Abs(x), assumption, budget=B) == expected


def test_principal_roots_and_logarithms():
    square = s.Pow(x**2, s.S.Half, evaluate=False)
    assert refine(square, s.Q.real(x), budget=B) == s.Abs(x)
    assert refine(square, s.Q.negative(x), budget=B) == -x
    assert refine(square, budget=B) == square
    assert refine(s.sqrt(x**6), s.Q.real(x), budget=B) == s.Abs(x) ** 3
    e = s.log(x**2, evaluate=False)
    assert refine(e, x > 0, budget=B) == 2 * s.log(x)
    assert refine(e, x < 0, budget=B) == e
    assert refine(s.log(s.exp(z)), budget=B) == s.log(s.exp(z))
    assert refine(s.log(s.exp(z)), s.Q.real(z), budget=B) == z
    # Actual values on the negative axis/principal logarithm strip.
    assert square.subs(x, -2) == 2
    assert s.log(s.exp(3 * s.pi * s.I)) != 3 * s.pi * s.I


def test_exp_log_requires_nonzero_and_does_not_fill_zero():
    e = s.exp(s.log(x, evaluate=False), evaluate=False)
    assert refine(e, budget=B) == e
    assert refine(e, s.Ne(x, 0), budget=B) == x
    assert refine(e, s.Eq(x, 0), budget=B) == e


@pytest.mark.parametrize(
    "head,assumption,expected",
    [
        (s.conjugate, s.Q.real(x), x),
        (s.conjugate, s.Q.imaginary(x), -x),
        (s.re, s.Q.real(x), x),
        (s.im, s.Q.real(x), s.S.Zero),
        (s.re, s.Q.imaginary(x), s.S.Zero),
        (s.im, s.Q.imaginary(x), -s.I * x),
        (s.floor, s.Q.integer(x), x),
        (s.ceiling, s.Q.integer(x), x),
        (s.sign, x > 0, s.S.One),
        (s.sign, x < 0, -s.S.One),
        (s.sign, s.Eq(x, 0), s.S.Zero),
        (s.arg, x > 0, s.S.Zero),
        (s.arg, x < 0, s.pi),
    ],
)
def test_component_rules(head, assumption, expected):
    assert refine(head(x, evaluate=False), assumption, budget=B) == expected


def test_arg_zero_is_not_assigned_a_value():
    e = s.arg(x, evaluate=False)
    assert refine(e, s.Eq(x, 0), budget=B) == e


def test_parity_and_integer_pi():
    assert refine(s.Pow(-1, x, evaluate=False), s.Q.even(x), budget=B) == 1
    assert refine(s.Pow(-1, x, evaluate=False), s.Q.odd(x), budget=B) == -1
    assert refine(s.sin(s.pi * x), s.Q.integer(x), budget=B) == 0
    assert refine(s.cos(s.pi * x), s.Q.odd(x), budget=B) == -1
    assert refine(s.cos(s.pi * x), s.Q.integer(x), budget=B) == (-1) ** x


def test_nested_piecewise_branch_context_and_order():
    e = s.Piecewise((s.Abs(x), x < 0), (s.Abs(x), True), evaluate=False)
    r = refine(e, budget=B)
    assert r == s.Piecewise((-x, x < 0), (x, True), evaluate=False)
    assert refine(e, x > 0, budget=B) == x
    e = s.Piecewise((1, x > 0), (2, x > 1), (3, True), evaluate=False)
    r = refine(e, budget=B)
    assert r.subs(x, 2) == 1
    assert r.subs(x, -1) == 3
    # No assumptions from a later branch may affect the first one.
    assert (
        refine(
            s.Piecewise((s.sqrt(x * x), x > 0), (s.sqrt(x * x), True)), budget=B
        ).subs(x, -2)
        == 2
    )


def test_contradictions_global_context_and_bound_symbols():
    e = s.Abs(x)
    for a in (False, (x > 0) & (x < 0), s.Q.positive(x) & s.Q.zero(x)):
        r = refine(e, a, budget=B, return_result=True)
        assert r.expression == e and r.stopped == "inconsistent assumptions"
    p = s.Symbol("p", positive=True)
    e = s.Abs(p, evaluate=False)
    assert refine(e, s.Q.negative(p), budget=B) == e
    with assuming(s.Q.positive(x)):
        assert refine(s.Abs(x), budget=B) == s.Abs(x)
    integral = s.Integral(s.Abs(x), (x, -1, 1))
    assert refine(integral, x > 0, budget=B) == integral


def test_no_core_delegation_to_sympy_refine(monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("SymPy refine called")

    monkeypatch.setattr(s, "refine", forbidden)
    module = importlib.import_module("sympy.assumptions.refine")
    monkeypatch.setattr(module, "refine", forbidden)
    assert refine(s.sqrt(x * x), s.Q.positive(x), budget=B) == x
    assert refine(s.log(s.exp(x)), s.Q.real(x), budget=B) == x


def test_unevaluated_singular_structure_is_retained():
    e = s.Mul(x, s.Pow(x, -1, evaluate=False), evaluate=False)
    assert refine(e, budget=B) == e


def test_refinement_budgets():
    e = s.Abs(x)
    for budget in (
        SimplificationBudget(seconds=0),
        SimplificationBudget(max_steps=0),
        SimplificationBudget(max_ops=0),
    ):
        assert refine(e, x > 0, budget=budget) == e
    r = refine(
        s.Abs(x) + s.Abs(z),
        (x > 0) & (z > 0),
        budget=SimplificationBudget(max_steps=1, seconds=5),
        return_result=True,
    )
    assert r.steps <= 1 and len(r.evidence) == r.steps


def test_affine_contradictions_are_inconclusive():
    for assumptions in ((x > 1) & (x < 0), s.Q.positive(x - 1) & s.Q.negative(x)):
        r = refine(s.Abs(x), assumptions, budget=B, return_result=True)
        assert r.expression == s.Abs(x) and r.stopped == "inconsistent assumptions"


@pytest.mark.parametrize(
    "assumptions,points",
    [
        (s.Q.positive(x), [s.Rational(1, 3), 2, 7]),
        (s.Q.negative(x), [-s.Rational(1, 3), -2, -7]),
        (s.Q.real(x), [-3, 0, s.Rational(2, 3)]),
    ],
)
def test_numeric_witnesses_for_guarded_rules(assumptions, points):
    expressions = [
        s.Abs(x),
        s.sqrt(x * x),
        s.sign(x),
        s.conjugate(x),
        s.re(x),
        s.im(x),
        s.log(s.exp(x)),
    ]
    for expression in expressions:
        result = refine(expression, assumptions, budget=B)
        for value in points:
            assert abs(complex((expression - result).subs(x, value).evalf(40))) < 1e-30


def test_boolean_refinement():
    assert refine(x > 0, x > 1, budget=B) == s.true
    assert refine(x < 0, x > 0, budget=B) == s.false


def test_predicate_proofs_do_not_erase_undefined_arguments():
    for e in (s.im(1 / x, evaluate=False), s.sign(s.exp(1 / x), evaluate=False)):
        assert refine(e, s.Q.real(x), budget=B) == e
    e = s.im(1 / x, evaluate=False)
    assert refine(e, s.Q.real(x) & s.Ne(x, 0), budget=B) == 0
    condition = s.Eq(1 / x, 1 / x, evaluate=False)
    assert refine(condition, budget=B) == condition
    e = s.Piecewise((1, condition), (2, True), evaluate=False)
    assert refine(e, budget=B) == e


def test_tangent_integer_pi():
    assert refine(s.tan(s.pi * x), s.Q.integer(x), budget=B) == 0
