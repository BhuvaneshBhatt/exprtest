"""Cross-check specialized exact stages against independent exact methods."""

import random

import pytest
import sympy as sp

from exprtest import Verdict, zerotest
from exprtest._algebraic import exact_algebraic_number_test
from exprtest._sqrt_sum import square_root_sum_test


@pytest.mark.parametrize(
    "expr",
    [
        sp.Add(sp.sqrt(2), sp.sqrt(8), -3 * sp.sqrt(2), evaluate=False),
        sp.Add(sp.sqrt(2), sp.sqrt(3), -sp.sqrt(5), evaluate=False),
        sp.Add(2 * sp.sqrt(12), -4 * sp.sqrt(3), evaluate=False),
        sp.Add(sp.Rational(3, 2), sp.sqrt(7), evaluate=False),
    ],
)
def test_square_root_fast_path_agrees_with_general_algebraic_engine(expr):
    fast = square_root_sum_test(expr)
    general = exact_algebraic_number_test(expr)
    assert fast.verdict in {Verdict.ZERO_PROVEN, Verdict.NONZERO_PROVEN}
    assert general.verdict is fast.verdict


def test_small_generated_square_root_sums_agree_with_exact_engine():
    rng = random.Random(20260828)
    radicands = [2, 3, 5, 6, 7]
    for _ in range(12):
        parts = []
        for rad in rng.sample(radicands, 3):
            coeff = rng.choice([-2, -1, 1, 2])
            parts.append(coeff * sp.sqrt(rad))
        expr = sp.Add(*parts, evaluate=False)
        fast = square_root_sum_test(expr)
        general = exact_algebraic_number_test(expr)
        assert fast.verdict is Verdict.NONZERO_PROVEN
        assert general.verdict is Verdict.NONZERO_PROVEN


def test_rational_function_identity_matches_exact_numerator_test():
    x = sp.symbols("x")
    exprs = [
        1 / x + 1 / (x + 1) - (2 * x + 1) / (x * (x + 1)),
        (x**2 - 1) / (x - 1) - (x + 1),
        (x + 2) / (x + 3) - (x + 1) / (x + 3),
    ]
    for expr in exprs:
        num, _ = sp.cancel(expr).as_numer_denom()
        expected = bool(num == 0)
        assert zerotest(expr, seed=1, use_cache=False) is expected
