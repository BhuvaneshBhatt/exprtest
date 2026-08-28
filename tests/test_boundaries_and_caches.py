"""Boundary, refusal, and cache-discipline tests for bounded proof stages."""

import sympy as sp

from exprtest import Verdict, _cache
from exprtest import _config as cfg
from exprtest._exp_independence import _algebraic_nonzero
from exprtest._negative_cache import (
    clear_negative_cache,
    exp_indep_inapplicable,
    log_rel_inapplicable,
    sqrt_sum_inapplicable,
)
from exprtest._sqrt_sum import square_root_sum_test

_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]


def _sqrt_sum(count):
    return sp.Add(*(sp.sqrt(p) for p in _PRIMES[:count]), evaluate=False)


def test_square_root_term_budget_boundary():
    admitted = square_root_sum_test(_sqrt_sum(cfg.SQRT_SUM_MAX_TERMS))
    refused = square_root_sum_test(_sqrt_sum(cfg.SQRT_SUM_MAX_TERMS + 1))
    assert admitted.verdict is Verdict.NONZERO_PROVEN
    assert refused.verdict is Verdict.UNKNOWN


def test_square_root_radicand_bit_boundary():
    inside = 2 ** (cfg.SQRT_SUM_RAD_BITS - 1) - 1
    outside = 2**cfg.SQRT_SUM_RAD_BITS + 1
    admitted = sp.Add(sp.sqrt(inside), sp.Integer(1), evaluate=False)
    refused = sp.Add(sp.sqrt(outside), sp.Integer(1), evaluate=False)
    assert square_root_sum_test(admitted).verdict is Verdict.NONZERO_PROVEN
    assert square_root_sum_test(refused).verdict is Verdict.UNKNOWN


def test_exponent_gap_refuses_expression_over_operation_budget():
    factors = [sp.Add(sp.sqrt(2), sp.Integer(i), evaluate=False) for i in range(1, 30)]
    expr = sp.Mul(*factors, evaluate=False)
    assert int(expr.count_ops()) > cfg.EXP_INDEP_GAP_MAX_OPS
    assert _algebraic_nonzero(expr) is None


def test_negative_applicability_caches_record_and_clear_results():
    x = sp.symbols("x")
    clear_negative_cache()
    exp_indep_inapplicable.cache_clear()
    log_rel_inapplicable.cache_clear()
    sqrt_sum_inapplicable.cache_clear()

    assert exp_indep_inapplicable(x + 1) is True
    assert log_rel_inapplicable(x + 1) is True
    assert sqrt_sum_inapplicable(x + 1) is True
    assert exp_indep_inapplicable.cache_info().currsize == 1
    assert log_rel_inapplicable.cache_info().currsize == 1
    assert sqrt_sum_inapplicable.cache_info().currsize == 1

    clear_negative_cache()
    assert exp_indep_inapplicable.cache_info().currsize == 0
    assert log_rel_inapplicable.cache_info().currsize == 0
    assert sqrt_sum_inapplicable.cache_info().currsize == 0


def test_global_cache_clear_resets_new_exact_and_negative_caches():
    expr = sp.sqrt(2) + sp.sqrt(3)
    square_root_sum_test(expr)
    _algebraic_nonzero(sp.sqrt(2) - sp.sqrt(3))
    sqrt_sum_inapplicable(sp.Symbol("x") + 1)
    _cache.cache_clear()
    assert _algebraic_nonzero.cache_info().currsize == 0
    assert sqrt_sum_inapplicable.cache_info().currsize == 0
