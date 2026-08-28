import sympy as sp

from exprtest._cache import cache_clear
from exprtest._result import Verdict

x, y, z = sp.symbols("x y z")


def setup_function(_):
    cache_clear()


# --------------------------------------------------------------------------
# Exact algebraic reduction pipeline
# --------------------------------------------------------------------------


def test_algebraic_expression_classifier_rejects_inexact_values():
    from exprtest._algebraic import classify_algebraic_expression

    exact = classify_algebraic_expression(sp.sqrt(2) + sp.sqrt(3))
    inexact = classify_algebraic_expression(sp.Float("1.41421356237"))
    symbolic = classify_algebraic_expression(sp.sqrt(x))
    assert exact.is_algebraic and exact.is_simple
    assert not inexact.is_algebraic
    assert not symbolic.is_algebraic


def test_algebraic_model_extracts_generators_and_minpolys():
    from exprtest._algebraic import build_algebraic_model

    expr = sp.sqrt(2) + sp.sqrt(3)
    model = build_algebraic_model(expr)
    assert model is not None
    assert set(model.generators) == {sp.sqrt(2), sp.sqrt(3)}
    assert sorted(poly.degree() for poly in model.minpolys) == [2, 2]
    assert model.degree_product == 4


def test_minpoly_remainder_proves_root_relation_without_common_field():
    from exprtest._algebraic import algebraic_relation_reduction_test

    t = sp.symbols("t")
    root = sp.CRootOf(t**3 - 2, 0)
    expr = sp.Add(sp.Pow(root, 3, evaluate=False), -2, evaluate=False)
    result = algebraic_relation_reduction_test(expr)
    assert result.verdict is Verdict.ZERO_PROVEN
    assert result.method == "algebraic-remainder"


def test_nonzero_independent_generator_remainder_is_inconclusive():
    from exprtest._algebraic import algebraic_relation_reduction_test

    result = algebraic_relation_reduction_test(sp.sqrt(2) + sp.sqrt(3))
    assert result.verdict is Verdict.UNKNOWN


def test_common_number_field_resolves_generator_dependency():
    from exprtest._algebraic import common_number_field_test

    expr = sp.sqrt(2) + sp.sqrt(3) - sp.sqrt(5 + 2 * sp.sqrt(6))
    result = common_number_field_test(expr)
    assert result.verdict is Verdict.ZERO_PROVEN
    assert result.method == "algebraic-common-field"


def test_common_number_field_proves_nonzero_algebraic_value():
    from exprtest._algebraic import common_number_field_test

    result = common_number_field_test(sp.sqrt(2) + sp.sqrt(3))
    assert result.verdict is Verdict.NONZERO_PROVEN


def test_exact_algebraic_pipeline_uses_relation_reduction_first():
    from exprtest._algebraic import exact_algebraic_number_test

    t = sp.symbols("t")
    root = sp.CRootOf(t**4 - 10, 0)
    expr = sp.Add(sp.Pow(root, 4, evaluate=False), -10, evaluate=False)
    result = exact_algebraic_number_test(expr)
    assert result.verdict is Verdict.ZERO_PROVEN
    assert result.method == "algebraic-remainder"


# --------------------------------------------------------------------------
# Algebraic root-set, radical, separation, and reduction utilities
# --------------------------------------------------------------------------


def test_complete_root_set_uses_symmetric_coefficient_identities():
    from exprtest._algebraic import simplify_root_sets

    u = sp.symbols("u")
    roots = [sp.CRootOf(u**3 - u + 1, pos) for pos in range(3)]
    assert simplify_root_sets(sum(roots)) == 0
    assert simplify_root_sets(sp.Mul(*roots)) == -1


def test_majority_root_set_rewrites_through_complement():
    from exprtest._algebraic import simplify_root_sets

    u = sp.symbols("u")
    roots = [sp.CRootOf(u**3 - u + 1, pos) for pos in range(3)]
    reduced = simplify_root_sets(roots[0] + roots[1])
    assert reduced == -roots[2]


def test_half_or_smaller_root_set_is_left_unchanged():
    from exprtest._algebraic import simplify_root_sets

    u = sp.symbols("u")
    roots = [sp.CRootOf(u**4 + u + 1, pos) for pos in range(4)]
    partial = roots[0] + roots[1]
    assert simplify_root_sets(partial) == partial


def test_majority_root_product_uses_complement():
    from exprtest._algebraic import simplify_root_sets

    u = sp.symbols("u")
    roots = [sp.CRootOf(u**3 - u + 1, pos) for pos in range(3)]
    reduced = simplify_root_sets(roots[0] * roots[1])
    assert len(reduced.atoms(sp.CRootOf)) == 1
    assert reduced == -1 + roots[2] ** 2


def test_rational_radicals_share_prime_power_basis():
    from exprtest._algebraic import normalize_radicals

    raw = sp.Pow(sp.Rational(8), sp.Rational(1, 4), evaluate=False)
    normalized = normalize_radicals(raw)
    assert normalized == sp.Pow(2, sp.Rational(3, 4))


def test_algebraic_gap_bound_is_positive_and_valid():
    from exprtest._algebraic import algebraic_gap_bound

    gap = algebraic_gap_bound(sp.sqrt(2))
    assert gap is not None
    assert gap.lower > 0
    assert float(gap.lower) <= float(sp.sqrt(2))
    assert gap.polynomial.eval(sp.sqrt(2)) == 0


def test_algebraic_gap_test_proves_nonzero():
    from exprtest._algebraic import algebraic_gap_test

    result = algebraic_gap_test(sp.sqrt(2) - 1)
    assert result.verdict is Verdict.NONZERO_PROVEN
    assert result.evidence == "algebraic-separation"


def test_exact_pipeline_can_use_root_set_preprocessing():
    from exprtest._algebraic import exact_algebraic_number_test

    u = sp.symbols("u")
    roots = [sp.CRootOf(u**3 - u + 1, pos) for pos in range(3)]
    result = exact_algebraic_number_test(sum(roots))
    assert result.verdict is Verdict.ZERO_PROVEN


# --------------------------------------------------------------------------
# Triangular algebraic towers and strengthened separation bounds
# --------------------------------------------------------------------------


def test_nested_radical_tower_reduces_defining_relation():
    from exprtest._algebraic import build_algebraic_tower, tower_algebraic_test

    inner = sp.Pow(2, sp.Rational(1, 2), evaluate=False)
    outer = sp.Pow(1 + inner, sp.Rational(1, 2), evaluate=False)
    expr = sp.Add(sp.Pow(outer, 2, evaluate=False), -1, -inner, evaluate=False)
    tower = build_algebraic_tower(expr)
    assert tower is not None
    assert len(tower.steps) == 2
    result = tower_algebraic_test(expr)
    assert result.verdict is Verdict.ZERO_PROVEN
    assert result.evidence == "triangular-algebraic-reduction"


def test_nested_radical_tower_can_prove_real_sign():
    from exprtest._algebraic import tower_algebraic_test

    inner = sp.Pow(2, sp.Rational(1, 2), evaluate=False)
    outer = sp.Pow(1 + inner, sp.Rational(1, 2), evaluate=False)
    result = tower_algebraic_test(sp.Add(outer, -1, evaluate=False))
    assert result.verdict is Verdict.NONZERO_PROVEN
    assert result.evidence in {"triangular-sign", "triangular-algebraic-nonzero"}


def test_fujiwara_candidate_can_improve_cauchy_gap():
    from exprtest._algebraic import algebraic_gap_bound

    u = sp.symbols("u")
    root = sp.CRootOf(100 * u**3 + 1, 0)
    gap = algebraic_gap_bound(root)
    assert gap is not None
    assert gap.method in {"reciprocal-fujiwara", "reciprocal-dyadic"}
    assert gap.lower >= sp.Rational(1, 10)


def test_gap_bound_never_exceeds_sampled_root_magnitude():
    from exprtest._algebraic import algebraic_gap_bound

    u = sp.symbols("u")
    roots = [sp.CRootOf(100 * u**3 + 1, pos) for pos in range(3)]
    for root in roots:
        gap = algebraic_gap_bound(root)
        assert gap is not None
        assert sp.N(abs(root), 80) >= sp.N(gap.lower, 80)


# --------------------------------------------------------------------------
# Algebraic growth control and conjugate-product bounds
# --------------------------------------------------------------------------


def test_algebraic_model_prunes_cancelled_generators():
    from exprtest._algebraic import build_algebraic_model

    expr = sp.Add(sp.sqrt(2), -sp.sqrt(2), sp.sqrt(3), evaluate=False)
    model = build_algebraic_model(expr)
    assert model is not None
    assert model.generators == (sp.sqrt(3),)


def test_high_power_algebraic_reduction_uses_exact_modular_powering():
    from exprtest._algebraic import algebraic_relation_reduction_test

    t = sp.symbols("t")
    root = sp.CRootOf(t**2 - 2, 0)
    expr = sp.Add(
        sp.Pow(root, 80, evaluate=False), -(sp.Integer(2) ** 40), evaluate=False
    )
    result = algebraic_relation_reduction_test(expr)
    assert result.verdict is Verdict.ZERO_PROVEN


def test_model_prunes_generators_cancelled_before_modeling():
    from exprtest._algebraic_model import build_algebraic_model

    a = sp.sqrt(2)
    b = sp.sqrt(3)
    cancelled = sp.Mul(a, b, evaluate=False)
    expr = sp.Add(cancelled, -cancelled, sp.sqrt(5), evaluate=False)
    model = build_algebraic_model(expr)
    assert model is not None
    assert len(model.generators) <= 1


def test_square_root_sum_fast_path_proves_nonzero():
    from exprtest import profile_zerotest
    from exprtest._sqrt_sum import square_root_sum_test

    expr = sp.sqrt(2) + sp.sqrt(3) - sp.sqrt(5)
    result = square_root_sum_test(expr)
    assert result.verdict is Verdict.NONZERO_PROVEN
    profile = profile_zerotest(expr)
    assert profile.result is False
    assert profile.method == "sqrt-sum"


def test_square_root_sum_combines_unsimplified_radicands():
    from exprtest._sqrt_sum import square_root_sum_test

    expr = sp.Add(
        sp.Pow(8, sp.Rational(1, 2), evaluate=False),
        -2 * sp.sqrt(2),
        evaluate=False,
    )
    result = square_root_sum_test(expr)
    assert result.verdict is Verdict.ZERO_PROVEN


def test_quadratic_nested_radical_pre_denests_exactly():
    from exprtest._algebraic_normalize import denest_quadratic_radical

    expr = sp.Pow(3 + 2 * sp.sqrt(2), sp.Rational(1, 2), evaluate=False)
    assert denest_quadratic_radical(expr) == 1 + sp.sqrt(2)


def test_quadratic_nested_radical_rejects_nonsquare_discriminant():
    from exprtest._algebraic_normalize import denest_quadratic_radical

    expr = sp.Pow(4 + sp.sqrt(2), sp.Rational(1, 2), evaluate=False)
    assert denest_quadratic_radical(expr) == expr
