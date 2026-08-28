import sympy as sp

from exprtest import Verdict, profile_zerotest, zerotest
from exprtest._cache import cache_clear

x, y, z = sp.symbols("x y z")


def setup_function(_):
    cache_clear()


# --------------------------------------------------------------------------
# Exact transcendental zero sets and branch-safe logarithms
# --------------------------------------------------------------------------


def test_unevaluated_periodic_zero_is_proven_exactly():
    from exprtest._transcendental import transcendental_zero_test

    arg = sp.Mul(7, sp.pi, evaluate=False)
    expr = sp.sin(arg, evaluate=False)
    result = transcendental_zero_test(expr)
    assert result.verdict is Verdict.ZERO_PROVEN


def test_periodic_zero_uses_integer_assumption():
    from exprtest._transcendental import transcendental_zero_test

    n = sp.symbols("n")
    expr = sp.sin(sp.Mul(sp.pi, n, evaluate=False), evaluate=False)
    result = transcendental_zero_test(expr, sp.Q.integer(n))
    assert result.verdict is Verdict.ZERO_PROVEN


def test_positive_log_power_normalizes_without_forcing_branches():
    from exprtest._transcendental import normalize_logs

    p = sp.symbols("p", positive=True)
    expr = sp.Add(
        sp.log(sp.Pow(p, 2, evaluate=False), evaluate=False),
        -2 * sp.log(p),
        evaluate=False,
    )
    assert normalize_logs(expr) == 0


def test_log_power_is_not_split_without_positive_base():
    from exprtest._transcendental import normalize_logs

    q = sp.symbols("q")
    expr = sp.log(sp.Pow(q, 2, evaluate=False), evaluate=False)
    assert normalize_logs(expr) == expr


def test_exact_algebraic_sign_and_comparison():
    from exprtest._exact_constants import algebraic_sign, compare_algebraic

    assert algebraic_sign(sp.sqrt(2) - sp.Rational(7, 5)) == 1
    assert algebraic_sign(sp.sqrt(2) - sp.sqrt(3)) == -1
    assert algebraic_sign(sp.sqrt(2) - sp.sqrt(2)) == 0
    cmp = compare_algebraic(sp.sqrt(3), sp.sqrt(2))
    assert cmp is not None and cmp.order == 1


def test_canonicalize_nested_algebraic_constant():
    from exprtest._exact_constants import canonical_algebraic

    expr = sp.sqrt(2) + sp.sqrt(3) - sp.sqrt(5 + 2 * sp.sqrt(6))
    assert canonical_algebraic(expr) == 0


def test_rational_pi_trig_constant_reduction_is_exact():
    from exprtest._exact_constants import reduce_exact_trig

    expr = sp.Add(sp.cos(2 * sp.pi / 7), -sp.cos(2 * sp.pi / 7), evaluate=False)
    reduced = reduce_exact_trig(expr)
    assert reduced == 0


def test_rational_pi_trig_constant_respects_degree_budget():
    from exprtest._exact_constants import reduce_exact_trig

    expr = sp.sin(sp.pi / 17)
    assert reduce_exact_trig(expr, degree_limit=4) == expr
    reduced = reduce_exact_trig(expr, degree_limit=32)
    assert isinstance(reduced, sp.AlgebraicNumber)
    assert reduced.as_expr() == expr


# --------------------------------------------------------------------------
# Cyclotomic arithmetic and closed logarithmic constants
# --------------------------------------------------------------------------


def test_cyclotomic_reduction_proves_seventh_root_cosine_identity():
    from exprtest._cyclotomic import cyclotomic_form, cyclotomic_zero_test

    expr = (
        sp.cos(2 * sp.pi / 7)
        + sp.cos(4 * sp.pi / 7)
        + sp.cos(6 * sp.pi / 7)
        + sp.Rational(1, 2)
    )
    form = cyclotomic_form(expr)
    assert form is not None
    assert form.is_zero
    result = cyclotomic_zero_test(expr)
    assert result.verdict is Verdict.ZERO_PROVEN
    assert result.evidence == "cyclotomic-polynomial-reduction"


def test_root_of_unity_arithmetic_reduces_exactly():
    from exprtest._cyclotomic import cyclotomic_zero_test

    root = sp.exp(2 * sp.pi * sp.I / 5, evaluate=False)
    expr = sp.Add(
        sum(sp.Pow(root, k, evaluate=False) for k in range(5)), evaluate=False
    )
    result = cyclotomic_zero_test(expr)
    assert result.verdict is Verdict.ZERO_PROVEN


def test_log_dependence_detects_exact_positive_algebraic_relation():
    from exprtest._transcendental import log_dependence_test

    expr = sp.Add(
        sp.log(2 + sp.sqrt(3), evaluate=False),
        sp.log(2 - sp.sqrt(3), evaluate=False),
        evaluate=False,
    )
    result = log_dependence_test(expr)
    assert result.verdict is Verdict.ZERO_PROVEN
    assert result.evidence == "exact-log-multiplicative-relation"


def test_log_dependence_can_prove_nonzero_relation():
    from exprtest._transcendental import log_dependence_test

    expr = sp.Add(sp.log(2, evaluate=False), -sp.log(3, evaluate=False), evaluate=False)
    result = log_dependence_test(expr)
    assert result.verdict is Verdict.NONZERO_PROVEN


def test_closed_exp_log_normalization_respects_real_principal_branch():
    from exprtest._transcendental import normalize_exp_log

    value = sp.sqrt(3)
    expr = sp.log(sp.exp(value, evaluate=False), evaluate=False)
    assert normalize_exp_log(expr) == value


def test_closed_exp_log_normalization_handles_positive_algebraic_base():
    from exprtest._transcendental import normalize_exp_log

    base = sp.sqrt(2)
    expr = sp.exp(sp.log(base, evaluate=False), evaluate=False)
    assert normalize_exp_log(expr) == base


def test_main_cascade_uses_cyclotomic_identity_stage():
    expr = (
        sp.cos(2 * sp.pi / 7)
        + sp.cos(4 * sp.pi / 7)
        + sp.cos(6 * sp.pi / 7)
        + sp.Rational(1, 2)
    )
    result = profile_zerotest(expr)
    assert result.result is True
    assert any(stage.stage == "cyclotomic" for stage in result.stages)


def test_main_cascade_uses_log_dependence_stage():
    expr = sp.Add(
        sp.log(2 + sp.sqrt(3), evaluate=False),
        sp.log(2 - sp.sqrt(3), evaluate=False),
        evaluate=False,
    )
    result = profile_zerotest(expr)
    assert result.result is True
    assert any(stage.stage == "transcendental" for stage in result.stages)


def test_exp_of_positive_log_sum_normalizes_to_algebraic_product():
    from exprtest._transcendental import normalize_exp_log

    expr = sp.exp(
        sp.Add(sp.log(2, evaluate=False), sp.log(3, evaluate=False), evaluate=False),
        evaluate=False,
    )
    assert normalize_exp_log(expr) == 6


def test_log_exp_uses_exact_principal_strip_for_complex_constant():
    from exprtest._transcendental import normalize_exp_log

    value = sp.Add(2, sp.I * sp.pi / 3, evaluate=False)
    expr = sp.log(sp.exp(value, evaluate=False), evaluate=False)
    assert sp.expand(normalize_exp_log(expr) - value) == 0


def test_log_exp_does_not_cross_negative_principal_boundary():
    from exprtest._transcendental import normalize_exp_log

    value = -sp.I * sp.pi
    expr = sp.log(sp.exp(value, evaluate=False), evaluate=False)
    assert normalize_exp_log(expr) != value


def test_zerotest_is_proof_oriented_tri_state():
    from exprtest import zerotest

    x = sp.symbols("x")
    assert zerotest(0, use_cache=False) is True
    assert zerotest(sp.pi, use_cache=False) is False
    assert zerotest(sp.Function("f")(x), use_cache=False) is None


def test_number_kind_uses_cheap_transcendence_theorems():
    from exprtest import number_kind
    from exprtest._domains import NumberKind

    assert number_kind(sp.sqrt(2)) is NumberKind.ALGEBRAIC
    assert number_kind(sp.pi) is NumberKind.TRANSCENDENTAL
    assert number_kind(3 * sp.pi / 7) is NumberKind.TRANSCENDENTAL
    assert number_kind(sp.exp(sp.sqrt(2))) is NumberKind.TRANSCENDENTAL
    assert number_kind(sp.log(2)) is NumberKind.TRANSCENDENTAL
    assert number_kind(sp.sin(sp.Rational(1, 2))) is NumberKind.TRANSCENDENTAL


def test_number_kind_does_not_combine_two_transcendentals_unsafely():
    from exprtest import number_kind
    from exprtest._domains import NumberKind

    term = sp.Add(sp.pi, -sp.pi, evaluate=False)
    assert number_kind(term) is NumberKind.UNKNOWN


def test_elementof_strips_stable_domain_parts():
    from exprtest import ElementOf

    x = sp.symbols("x")
    assert ElementOf(sp.Add(x, 2, evaluate=False), sp.S.Integers) == sp.Contains(
        x, sp.S.Integers, evaluate=False
    )
    assert ElementOf(
        sp.Mul(sp.Rational(3, 2), x, evaluate=False), sp.S.Rationals
    ) == sp.Contains(x, sp.S.Rationals, evaluate=False)


def test_elementof_uses_transcendence_for_algebraic_membership():
    from exprtest import ElementOf
    from exprtest._domains import Algebraics

    assert ElementOf(sp.pi, Algebraics) is False
    assert ElementOf(sp.sqrt(2), Algebraics) is True


def test_fast_oracle_source_has_no_generic_simplify_call():
    import inspect

    import exprtest.core as core_mod

    source = inspect.getsource(core_mod)
    assert "sp.simplify" not in source
    assert "general_symbolic_simplification_test" not in source


def test_exact_budget_rejects_large_expression_before_exact_methods():
    from exprtest import zerotest

    xs = [sp.sqrt(sp.Integer(p)) for p in list(sp.primerange(2, 400))[:40]]
    term = sp.Add(*xs, evaluate=False)
    assert zerotest(term, use_cache=False) is None


def test_elementof_does_not_strip_nonunit_integer_factor():
    from exprtest import ElementOf

    x = sp.symbols("x")
    term = sp.Mul(2, x, evaluate=False)
    assert ElementOf(term, sp.S.Integers) == sp.Contains(
        term, sp.S.Integers, evaluate=False
    )


def test_zerotest_source_avoids_generic_simplify():
    import inspect

    from exprtest import core

    assert "sp.simplify" not in inspect.getsource(core)
    assert zerotest(sp.exp(sp.sqrt(2), evaluate=False), use_cache=False) is False


def test_elementof_reduces_rational_power_for_algebraic_membership():
    from exprtest import ElementOf
    from exprtest._domains import Algebraics

    x = sp.symbols("x")
    term = sp.Pow(x, sp.Rational(2, 3), evaluate=False)
    assert ElementOf(term, Algebraics) == sp.Contains(x, Algebraics, evaluate=False)


def test_gelfond_schneider_power_kind_and_difference():
    from exprtest import number_kind, zerotest
    from exprtest._domains import NumberKind

    value = sp.Pow(2, sp.sqrt(2), evaluate=False)
    assert number_kind(value) is NumberKind.TRANSCENDENTAL
    assert number_kind(value - 3) is NumberKind.TRANSCENDENTAL
    assert zerotest(value - 3, use_cache=False) is False


def test_rational_log_relation_fast_path_remains_exact():
    from exprtest._transcendental import rational_log_test

    zero = 2 * sp.log(2) - sp.log(4)
    nonzero = sp.log(2) - sp.log(3)
    assert rational_log_test(zero).verdict is Verdict.ZERO_PROVEN
    assert rational_log_test(nonzero).verdict is Verdict.NONZERO_PROVEN
