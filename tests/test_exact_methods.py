import sympy as sp

from exprtest import ElementOf, number_kind, zerotest
from exprtest._cache import cache_clear
from exprtest._cyclotomic import cyclotomic_zero_test
from exprtest._domains import (
    Algebraics,
    NumberKind,
    domain_facts,
    rational_transcendental_kind,
)
from exprtest._pslq import pslq_zero_relation
from exprtest._result import Verdict
from exprtest._special import reduce_special_values
from exprtest._transcendental import rational_log_test


def test_rational_function_in_pi_is_proven_transcendental():
    expr = (sp.pi**3 + 2 * sp.pi + 1) / (sp.pi**2 + 3)
    assert rational_transcendental_kind(expr) is NumberKind.TRANSCENDENTAL
    assert number_kind(expr) is NumberKind.TRANSCENDENTAL
    assert zerotest(expr, use_cache=False) is False


def test_rational_function_cancellation_can_be_algebraic():
    expr = sp.Mul(sp.pi, sp.Pow(sp.pi, -1, evaluate=False), evaluate=False)
    assert rational_transcendental_kind(expr) is NumberKind.ALGEBRAIC
    assert zerotest(expr, use_cache=False) is False


def test_exact_object_caches_record_reuse():
    from exprtest._memo import minpoly_for

    cache_clear()
    z = sp.Symbol("z")
    minpoly_for(sp.sqrt(2), z)
    minpoly_for(sp.sqrt(2), z)
    from exprtest._memo import _minpoly_expr

    assert _minpoly_expr.cache_info().hits >= 1


def test_pslq_relation_requires_exact_verification():
    expr = sp.Add(
        sp.cos(2 * sp.pi / 7),
        sp.cos(4 * sp.pi / 7),
        sp.cos(6 * sp.pi / 7),
        sp.Rational(1, 2),
        evaluate=False,
    )

    def verify(candidate):
        return cyclotomic_zero_test(candidate).verdict is Verdict.ZERO_PROVEN

    relation = pslq_zero_relation(expr, verify)
    assert relation is not None
    assert pslq_zero_relation(expr, lambda candidate: None) is None


def test_special_value_registry():
    g = sp.gamma(sp.Rational(5, 2), evaluate=False)
    z = sp.zeta(4, evaluate=False)
    assert reduce_special_values(g) == 3 * sp.sqrt(sp.pi) / 4
    assert reduce_special_values(z) == sp.pi**4 / 90
    expr = sp.Add(g, -3 * sp.sqrt(sp.pi) / 4, evaluate=False)
    assert zerotest(expr, use_cache=False) is True


def test_rational_log_prime_vectors():
    expr = sp.Add(
        sp.log(12, evaluate=False),
        -2 * sp.log(2, evaluate=False),
        -sp.log(3, evaluate=False),
        evaluate=False,
    )
    assert rational_log_test(expr).verdict is Verdict.ZERO_PROVEN
    assert zerotest(expr, use_cache=False) is True
    nonzero = sp.Add(
        sp.log(2, evaluate=False), -sp.log(3, evaluate=False), evaluate=False
    )
    assert rational_log_test(nonzero).verdict is Verdict.NONZERO_PROVEN


def test_richer_domain_facts_and_elementof():
    facts = domain_facts(sp.pi)
    assert facts.algebraic is False
    assert facts.real is True
    assert facts.nonzero is True
    assert ElementOf(sp.pi, Algebraics) is False
    root = sp.exp(2 * sp.pi * sp.I / 7, evaluate=False)
    assert domain_facts(root).root_of_unity is True
