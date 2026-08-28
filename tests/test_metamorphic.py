"""Metamorphic invariants for exact zero classification."""

import pytest
import sympy as sp

from exprtest import zerotest

x, y = sp.symbols("x y")
u, v = sp.symbols("u v")


@pytest.mark.parametrize(
    "expr,expected",
    [
        ((x + 1) * (x - 1) - x**2 + 1, True),
        (x**2 + 1, False),
        (sp.sqrt(2) + sp.sqrt(3) - sp.sqrt(5), False),
    ],
)
def test_exact_answer_survives_neutral_structure(expr, expected):
    forms = [
        expr,
        sp.Add(expr, sp.Integer(0), evaluate=False),
        sp.Mul(expr, sp.Integer(1), evaluate=False),
        sp.Mul(sp.Rational(7, 5), expr, evaluate=False),
    ]
    for form in forms:
        assert zerotest(form, use_cache=False) is expected


def test_symbol_renaming_preserves_exact_identity():
    expr = (x + y) ** 2 - x**2 - 2 * x * y - y**2
    renamed = expr.xreplace({x: u, y: v})
    assert zerotest(expr, use_cache=False) is True
    assert zerotest(renamed, use_cache=False) is True


def test_add_and_mul_argument_order_do_not_change_answer():
    add = sp.Add(sp.sqrt(2), sp.sqrt(3), -sp.sqrt(5), evaluate=False)
    rev_add = sp.Add(*reversed(add.args), evaluate=False)
    mul = sp.Mul(sp.Integer(3), sp.sqrt(2), evaluate=False)
    rev_mul = sp.Mul(*reversed(mul.args), evaluate=False)
    assert zerotest(add, use_cache=False) is False
    assert zerotest(rev_add, use_cache=False) is False
    assert zerotest(mul, use_cache=False) is False
    assert zerotest(rev_mul, use_cache=False) is False


def test_branch_sensitive_rewrite_is_not_a_metamorphic_identity():
    z = sp.symbols("z")
    unsafe = sp.sqrt(z**2) - z
    assert zerotest(unsafe, use_cache=False, confidence="certified") is None

    positive = sp.symbols("positive", positive=True)
    safe = sp.sqrt(positive**2) - positive
    assert zerotest(safe, use_cache=False) is True
