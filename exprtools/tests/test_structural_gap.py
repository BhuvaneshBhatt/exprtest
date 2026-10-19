"""Independent norm bounds and adversarial interval/domain regressions."""

import random
from unittest.mock import patch

import pytest
import sympy as sp

from exprtools import (
    SimplificationBudget,
    simplify,
    structural_separation_bound,
    zerotest,
)
from exprtools import _config as cfg
from exprtools._cache import cache_clear
from exprtools._result import Verdict
from exprtools._structural_gap import _bound_cached, structural_algebraic_test


def nested_zero(a=2, b=3):
    return sp.Add(
        sp.sqrt(a),
        sp.sqrt(b),
        -sp.Pow(a + b + 2 * sp.sqrt(a * b), sp.S.Half, evaluate=False),
        evaluate=False,
    )


def test_bound_is_conditional_and_does_not_establish_nonzero():
    e = nested_zero()
    bound = structural_separation_bound(e)
    assert bound is not None and bound.lower > 0
    assert (
        bound.bits == (bound.degree - 1) * bound.numerator_bits + bound.denominator_bits
    )
    assert bound.degree == 16
    assert not hasattr(bound, "verdict")


def test_shared_radicals_are_counted_once_in_degree_bound():
    root = sp.Pow(2, sp.S.Half, evaluate=False)
    e = sp.Add(root, sp.Mul(-1, root, evaluate=False), evaluate=False)
    assert structural_separation_bound(e).degree == 2


@pytest.mark.parametrize(
    "expr",
    [
        sp.Float("1.2"),
        sp.oo,
        sp.zoo,
        sp.nan,
        sp.Symbol("x"),
        sp.sin(1, evaluate=False),
        sp.Pow(2, -1, evaluate=False),
        sp.Pow(sp.Add(sp.sqrt(2), -sp.sqrt(2), evaluate=False), -1, evaluate=False),
        sp.Pow(2, sp.Rational(1, 100), evaluate=False),
        sp.Pow(2, 10000, evaluate=False),
        sp.Rational(1, 2**600),
    ],
)
def test_unsupported_or_undefined_inputs_are_declined(expr):
    assert structural_separation_bound(expr) is None
    assert structural_algebraic_test(expr).verdict is Verdict.UNKNOWN


def test_structural_caps_apply_before_cache_and_large_work():
    e = nested_zero()
    assert structural_separation_bound(e) is not None
    with patch.object(cfg, "STRUCTURAL_GAP_MAX_OPS", 0):
        assert structural_separation_bound(e) is None
    with patch.object(cfg, "STRUCTURAL_GAP_MAX_DEGREE", 2):
        assert structural_separation_bound(e) is None
    with patch.object(cfg, "STRUCTURAL_GAP_MAX_BITS", 1):
        assert structural_separation_bound(e) is None
    with patch.object(cfg, "EXACT_MAX_INT_BITS", 1):
        assert structural_separation_bound(sp.Rational(1, 8)) is None


@pytest.mark.flint
def test_nested_identities_do_not_construct_minimal_polynomials_or_factor():
    pytest.importorskip("flint")
    from exprtools import _memo

    def forbidden(*args, **kwargs):
        raise AssertionError("expensive algebraic backend called")

    for a, b in [(2, 3), (3, 5), (5, 7), (7, 11)]:
        with (
            patch.object(sp, "factorint", forbidden),
            patch.object(_memo, "minpoly_for", forbidden),
        ):
            result = structural_algebraic_test(nested_zero(a, b))
        assert result.verdict is Verdict.ZERO_PROVEN
        assert result.evidence == "structural-separation-and-enclosure"


@pytest.mark.flint
def test_nearby_nonzero_values_are_never_promoted_to_zero():
    pytest.importorskip("flint")
    e = nested_zero()
    for bits in (12, 80, 120, 200):
        result = structural_algebraic_test(
            sp.Add(e, sp.Rational(1, 2**bits), evaluate=False)
        )
        assert result.verdict in (Verdict.NONZERO_PROVEN, Verdict.UNKNOWN)
    tiny = sp.Add(
        sp.Pow(10**40 + 1, sp.S.Half, evaluate=False), -(10**20), evaluate=False
    )
    assert structural_algebraic_test(tiny).verdict is Verdict.NONZERO_PROVEN


@pytest.mark.flint
def test_principal_complex_root_is_not_replaced_by_a_real_root():
    pytest.importorskip("flint")
    cube = sp.Pow(-8, sp.Rational(1, 3), evaluate=False)
    equal = sp.Add(cube, -1, -sp.I * sp.sqrt(3), evaluate=False)
    unequal = sp.Add(cube, 2, evaluate=False)
    assert structural_algebraic_test(equal).verdict in (
        Verdict.ZERO_PROVEN,
        Verdict.UNKNOWN,
    )
    assert structural_algebraic_test(unequal).verdict in (
        Verdict.NONZERO_PROVEN,
        Verdict.UNKNOWN,
    )
    assert zerotest(unequal, confidence="certified") is not True


@pytest.mark.flint
def test_precision_restoration_and_strict_absolute_gap_comparison():
    flint = pytest.importorskip("flint")
    from exprtools import _numeric

    previous = flint.ctx.prec
    with patch.object(
        _numeric, "_sympy_to_acb_ball", side_effect=ValueError("unsupported")
    ):
        assert structural_algebraic_test(nested_zero()).verdict is Verdict.UNKNOWN
    assert flint.ctx.prec == previous
    wide = flint.acb(flint.arb("0 +/- 1"))
    with (
        patch.object(_numeric, "_sympy_to_acb_ball", return_value=wide),
        patch.object(cfg, "STRUCTURAL_GAP_MAX_PREC", cfg.INITIAL_PREC_BITS),
    ):
        assert structural_algebraic_test(sp.S.Zero).verdict is Verdict.UNKNOWN
    assert flint.ctx.prec == previous


def test_optional_backend_and_cache_lifecycle():
    from exprtools import _numeric

    e = nested_zero()
    structural_separation_bound(e)
    assert _bound_cached.cache_info().currsize
    with patch.object(_numeric, "flint", None):
        assert structural_algebraic_test(e).verdict is Verdict.UNKNOWN
    cache_clear()
    assert _bound_cached.cache_info().currsize == 0


@pytest.mark.flint
def test_general_simplifier_uses_certified_algebraic_reduction():
    pytest.importorskip("flint")
    e = nested_zero()
    result = simplify(
        e,
        transformations=["algebraic"],
        budget=SimplificationBudget(seconds=2),
        return_result=True,
    )
    assert result.expression == 0 and result.original == e and result.domain_preserved
    x = sp.Symbol("x")
    hole = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    assert simplify(hole, transformations=["algebraic"]) == hole


@pytest.mark.flint
def test_deterministic_exact_reference_matrix():
    pytest.importorskip("flint")
    rng = random.Random(20261018)
    variable = sp.Symbol("t")
    for _ in range(24):
        a, b = (rng.randrange(2, 14) for _ in range(2))
        e = sp.Add(
            sp.sqrt(a),
            -sp.sqrt(b),
            sp.Rational(rng.randrange(-4, 5), rng.randrange(1, 5)),
            evaluate=False,
        )
        result = structural_algebraic_test(e)
        if not result.proven:
            continue
        polynomial = sp.Poly(sp.minpoly(e, variable), variable)
        exact_zero = polynomial.degree() == 1 and polynomial.eval(0) == 0
        assert (result.verdict is Verdict.ZERO_PROVEN) == exact_zero
