import sympy as sp

from exprtest import profile_zerotest, zerotest
from exprtest._algebraic import (
    algebraic_gap_bound,
    build_algebraic_tower,
    tower_algebraic_test,
)
from exprtest._cache import cache_clear
from exprtest._call_memo import OracleMemo
from exprtest._defined import quick_defined_nonzero
from exprtest._exp_independence import exponential_independence_nonzero
from exprtest._features import expression_features
from exprtest._negative_cache import special_inapplicable
from exprtest._nonzero import quick_nonzero
from exprtest._normal_forms import exp_log_normal_form, log_normal_form
from exprtest._numeric import (
    _next_precision,
    _precision_from_expr,
    _precision_from_lower,
)
from exprtest._result import Verdict
from exprtest._rewrite import exact_rewrite
from exprtest._special import reduce_special_values
from exprtest._transcendental import log_dependence_test, rational_log_test


def test_quick_nonzero_short_circuits_exact_exponential():
    term = sp.exp(sp.sqrt(2), evaluate=False)
    assert quick_nonzero(term) is True
    profile = profile_zerotest(term)
    assert profile.result is False
    names = [stage.stage for stage in profile.stages]
    assert "quick-nonzero" in names
    assert "exact-algebraic" not in names


def test_expression_features_are_cached_and_route_structure():
    expression_features.cache_clear()
    term = sp.log(2, evaluate=False) + sp.sin(sp.pi / 7) + sp.sqrt(3)
    first = expression_features(term)
    before = expression_features.cache_info()
    second = expression_features(term)
    after = expression_features.cache_info()
    assert first == second
    assert first.has_log and first.has_trig and first.has_pi and first.has_radical
    assert after.hits == before.hits + 1


def test_shared_normal_forms_reuse_cached_results():
    term = sp.Add(
        sp.log(2, evaluate=False),
        sp.log(8, evaluate=False),
        -sp.log(16, evaluate=False),
        evaluate=False,
    )
    log_normal_form.cache_clear()
    first = log_normal_form(term)
    before = log_normal_form.cache_info()
    second = log_normal_form(term)
    after = log_normal_form.cache_info()
    assert first == second
    assert after.hits == before.hits + 1

    exp_term = sp.exp(sp.log(sp.Integer(7), evaluate=False), evaluate=False)
    assert exp_log_normal_form(exp_term) == 7


def test_algebraic_gap_has_cheap_then_refined_layers():
    x = sp.Symbol("x")
    root = sp.CRootOf(100 * x**3 + 1, 0)
    cheap = algebraic_gap_bound(root, refine=False)
    strong = algebraic_gap_bound(root, refine=True)
    assert cheap is not None and strong is not None
    assert cheap.method in {"reciprocal-cauchy", "reciprocal-fujiwara"}
    assert strong.lower >= cheap.lower


def test_separation_bound_selects_higher_start_precision():
    default = _precision_from_lower(sp.Rational(1, 2**20))
    hard = _precision_from_lower(sp.Rational(1, 2**700))
    assert default >= 80
    assert hard > default
    assert hard <= 2048


def test_tower_tracks_independent_subtree_supports():
    term = (sp.sqrt(2) + sp.sqrt(3)) / (1 + sp.sqrt(5))
    tower = build_algebraic_tower(term)
    assert tower is not None
    assert tower.numerator_support
    assert tower.denominator_support
    assert tower.numerator_support != tower.denominator_support
    assert len(tower.numerator_support) < len(tower.steps)
    assert len(tower.denominator_support) < len(tower.steps)


def test_symbolic_assumption_nonzero_uses_structural_engine():
    x = sp.symbols("x", positive=True)
    assert quick_nonzero(x) is True
    assert zerotest(x, use_cache=False) is False


def test_bounded_exponential_independence():
    expr = sp.Add(sp.exp(1), -sp.exp(2), evaluate=False)
    assert exponential_independence_nonzero(expr) is True
    assert zerotest(expr, use_cache=False) is False


def test_exponential_independence_rejects_equal_exponents():
    expr = sp.Add(sp.exp(1), -sp.exp(1), evaluate=False)
    assert exponential_independence_nonzero(expr) is None


def test_denominator_and_nonpole_facts():
    g = sp.gamma(sp.Rational(-1, 2), evaluate=False)
    pole = sp.gamma(sp.Integer(-2), evaluate=False)
    assert quick_defined_nonzero(g) is True
    assert quick_defined_nonzero(pole) is not True
    assert quick_defined_nonzero(sp.sqrt(2)) is True
    x = sp.Symbol("x", real=True)
    assert quick_defined_nonzero(x**2 + 1) is True


def test_call_local_memo_reuses_facts():
    memo = OracleMemo()
    expr = sp.sqrt(2) * sp.exp(1)
    first = memo.nonzero(expr)
    size = len(memo.nonzero_cache)
    second = memo.nonzero(expr)
    assert first is True and second is True
    assert len(memo.nonzero_cache) == size


def test_structural_precision_prediction_tracks_cancellation_risk():
    n = sp.Integer(2) ** 300
    hard = sp.sqrt(n + 1) - sp.sqrt(n)
    assert _precision_from_expr(hard) > _precision_from_expr(sp.sqrt(2))
    assert _next_precision(160, -100.0, 80, -20.0, sp.Rational(1, 2**180)) > 160


def test_exact_rewrite_registry():
    x = sp.Symbol("x", positive=True)
    assert exact_rewrite(sp.Abs(x, evaluate=False)) == x
    assert exact_rewrite(sp.conjugate(sp.Integer(3), evaluate=False)) == 3
    assert exact_rewrite(sp.sinh(0, evaluate=False)) == 0


def test_sparse_tower_reduction_nested_radicals():
    r2 = sp.Pow(2, sp.Rational(1, 2), evaluate=False)
    outer = sp.Pow(1 + r2, sp.Rational(1, 2), evaluate=False)
    expr = sp.Add(sp.Pow(outer, 2, evaluate=False), -(1 + r2), evaluate=False)
    tower = build_algebraic_tower(expr)
    assert tower is not None
    result = tower_algebraic_test(expr)
    assert result.verdict is Verdict.ZERO_PROVEN


def test_finite_float_literals_use_their_stored_value():
    assert zerotest(sp.Float(0.0), use_cache=False) is True
    assert zerotest(sp.Float(-0.0), use_cache=False) is True
    assert zerotest(sp.Float("1e-11"), use_cache=False) is False
    assert zerotest(sp.Float("1e-50"), use_cache=False) is False
    assert zerotest(sp.zoo, use_cache=False) is None


def test_profile_is_opt_in_and_reports_stages():
    profile = profile_zerotest(sp.pi + 1)
    assert profile.result is False
    assert profile.total_seconds >= 0
    assert profile.stages
    assert profile.stages[0].stage == "flint-direct"
    assert any(item.stage == "quick-reduce" for item in profile.stages)


def test_negative_applicability_cache_reuses_structure():
    cache_clear()
    expr = sp.Add(sp.pi, sp.sqrt(2), evaluate=False)
    zerotest(expr, use_cache=False)
    first = special_inapplicable.cache_info()
    zerotest(expr, use_cache=False)
    second = special_inapplicable.cache_info()
    assert second.hits > first.hits


def test_tower_nested_radical_zero():
    expr = sp.Add(sp.sqrt(2 + sp.sqrt(3)) ** 2, -2 - sp.sqrt(3), evaluate=False)
    result = tower_algebraic_test(expr)
    assert result.verdict is Verdict.ZERO_PROVEN
    assert zerotest(expr) is True


def test_tower_product_relation_zero():
    expr = sp.Add((1 + sp.sqrt(2)) * (sp.sqrt(2) - 1), -1, evaluate=False)
    assert tower_algebraic_test(expr).verdict is Verdict.ZERO_PROVEN


def test_dyadic_gap_sharpens_simple_cubic():
    x = sp.Symbol("x")
    root = sp.CRootOf(100 * x**3 + 1, 0)
    gap = algebraic_gap_bound(root)
    assert gap is not None
    assert gap.method == "reciprocal-dyadic"
    assert gap.lower > sp.Rational(1, 10)


def test_expanded_special_values():
    cases = [
        (sp.gamma(sp.Rational(-1, 2), evaluate=False), -2 * sp.sqrt(sp.pi)),
        (sp.factorial2(9, evaluate=False), sp.Integer(945)),
        (sp.binomial(-3, 4, evaluate=False), sp.Integer(15)),
        (sp.rf(sp.Rational(1, 2), 3, evaluate=False), sp.Rational(15, 8)),
        (sp.ff(sp.Rational(7, 2), 3, evaluate=False), sp.Rational(105, 8)),
        (sp.harmonic(5, evaluate=False), sp.Rational(137, 60)),
    ]
    for term, expected in cases:
        assert reduce_special_values(term) == expected
        assert zerotest(sp.Add(term, -expected, evaluate=False)) is True


def test_rational_log_radicals_reduce_to_prime_vector():
    expr = sp.Add(
        sp.log(sp.sqrt(2), evaluate=False),
        sp.log(sp.sqrt(8), evaluate=False),
        -sp.log(4, evaluate=False),
        evaluate=False,
    )
    result = rational_log_test(expr)
    assert result.verdict is Verdict.ZERO_PROVEN
    assert zerotest(expr) is True


def test_algebraic_unit_log_relation():
    expr = sp.Add(
        sp.log(2 + sp.sqrt(3), evaluate=False),
        sp.log(2 - sp.sqrt(3), evaluate=False),
        evaluate=False,
    )
    result = log_dependence_test(expr)
    assert result.verdict is Verdict.ZERO_PROVEN
    assert zerotest(expr) is True


def test_exponential_independence_uses_algebraic_separation_for_larger_exponents():
    left = sp.sqrt(2) + sp.sqrt(3)
    right = sp.sqrt(5) + sp.sqrt(7)
    assert int((left - right).count_ops()) > 4
    expr = sp.Add(sp.exp(left), -sp.exp(right), evaluate=False)
    assert exponential_independence_nonzero(expr) is True
    assert zerotest(expr, use_cache=False) is False


def test_new_structural_negative_caches():
    from exprtest._negative_cache import (
        exp_indep_inapplicable,
        log_rel_inapplicable,
        sqrt_sum_inapplicable,
    )

    assert exp_indep_inapplicable(sp.sqrt(2) + sp.sqrt(3)) is True
    assert exp_indep_inapplicable(sp.exp(1) + sp.exp(2)) is False
    assert log_rel_inapplicable(sp.exp(2) - 1) is True
    assert log_rel_inapplicable(sp.log(2) - sp.log(3)) is False
    assert sqrt_sum_inapplicable(sp.exp(1) + sp.exp(2)) is True
    assert sqrt_sum_inapplicable(sp.sqrt(2) + sp.sqrt(3)) is False
