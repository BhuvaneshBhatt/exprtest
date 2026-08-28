"""Stable structural performance contracts, not machine-speed benchmarks."""

from time import perf_counter

import pytest
import sympy as sp

from exprtest import _config as cfg
from exprtest._negative_cache import exp_indep_inapplicable, sqrt_sum_inapplicable
from exprtest._sqrt_sum import square_root_sum_test

pytestmark = pytest.mark.performance_contract


def test_inapplicable_stage_checks_are_bounded_on_large_plain_expression():
    x = sp.symbols("x")
    expr = sp.Add(*(x**i for i in range(1, 80)), evaluate=False)
    start = perf_counter()
    for _ in range(100):
        assert exp_indep_inapplicable(expr) is True
        assert sqrt_sum_inapplicable(expr) is True
    # This is deliberately generous: it catches accidental expensive symbolic
    # work while remaining stable on shared CI hosts.
    assert perf_counter() - start < 2.0


def test_square_root_fast_path_respects_term_budget_without_field_construction():
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]
    expr = sp.Add(
        *(sp.sqrt(p) for p in primes[: cfg.SQRT_SUM_MAX_TERMS + 1]), evaluate=False
    )
    start = perf_counter()
    result = square_root_sum_test(expr)
    assert result.method == "sqrt-sum"
    assert "budget" in result.detail
    assert perf_counter() - start < 1.0
