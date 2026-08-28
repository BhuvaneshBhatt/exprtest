import random
import time

import pytest
import sympy as sp

from exprtest import Verdict, ZeroClassification, profile_zerotest, zerotest
from exprtest._cache import _RESULT_CACHE, cache_clear, make_cache_key
from exprtest._finite_field import finite_field_identity_test
from exprtest._numeric import adaptive_precision_ball_test
from exprtest._timing import run_with_time_budget

x, y = sp.symbols("x y")

FLINT_AVAILABLE = __import__("importlib.util").util.find_spec("flint") is not None
requires_flint = pytest.mark.skipif(
    not FLINT_AVAILABLE, reason="python-flint is required"
)


def setup_function(_):
    cache_clear()


def test_literal_zero_and_nonzero():
    assert zerotest(sp.Integer(0)) is True
    assert zerotest(sp.Rational(3, 7)) is False


def test_closed_exact_identities():
    assert zerotest(sp.exp(sp.I * sp.pi) + 1, use_cache=False) is True
    assert zerotest(2 * sp.log(2) - sp.log(4), use_cache=False) is True
    expr = sp.sqrt(5 + 2 * sp.sqrt(6)) - (sp.sqrt(2) + sp.sqrt(3))
    assert zerotest(expr, use_cache=False) is True


def test_croot_relation():
    t = sp.symbols("t")
    root = sp.CRootOf(t**3 - 2, 0)
    assert zerotest(root**3 - 2, use_cache=False) is True


def test_profile_reports_fast_oracle_work():
    profile = profile_zerotest(sp.exp(sp.sqrt(2), evaluate=False))
    assert profile.result is False
    assert profile.total_seconds >= 0
    assert any(stage.stage == "quick-nonzero" for stage in profile.stages)


def test_cache_key_preserves_expression_and_target():
    expr = x**2 + 1
    loose = make_cache_key(expr, sp.true, 1e-6)
    strict = make_cache_key(expr, sp.true, 1e-12)
    assert loose[0] == expr
    assert loose != strict


def test_use_cache_false_does_not_populate_final_cache():
    assert len(_RESULT_CACHE) == 0
    zerotest(sp.Mul(x + 1, x + 2, evaluate=False), use_cache=False, seed=1)
    assert len(_RESULT_CACHE) == 0


def test_repeated_cached_calls_remain_inexpensive():
    expr = sp.sqrt(2) + sp.Rational(1, 3)
    start = time.perf_counter()
    zerotest(expr, use_cache=True)
    first = time.perf_counter() - start
    start = time.perf_counter()
    for _ in range(500):
        zerotest(expr, use_cache=True)
    repeated = time.perf_counter() - start
    assert repeated < first + 0.05


def test_nested_time_budget_preserves_outer_deadline():
    def inner_slow():
        time.sleep(5)

    def outer_work():
        run_with_time_budget(inner_slow, seconds=0.1, default=None)
        time.sleep(5)

    start = time.perf_counter()
    result = run_with_time_budget(outer_work, seconds=0.3, default="timed-out")
    assert result == "timed-out"
    assert time.perf_counter() - start < 0.4


def test_assumptions_refine_safe_identities():
    assert (
        zerotest(sp.Abs(x) - x, assumptions=sp.Q.positive(x), use_cache=False) is True
    )
    assert zerotest(x - y, assumptions=sp.Eq(x, y), use_cache=False) is True


def test_rng_and_seed_are_mutually_exclusive():
    with pytest.raises(ValueError):
        zerotest(x + 1, rng=random.Random(1), seed=1)


def test_seed_is_reproducible_for_public_verdict():
    first = zerotest(x + y + 1, use_cache=False, seed=12345)
    second = zerotest(x + y + 1, use_cache=False, seed=12345)
    assert first is second


def test_result_type_proof_semantics():
    likely = ZeroClassification(Verdict.NONZERO_LIKELY, "witness")
    unknown = ZeroClassification(Verdict.UNKNOWN, "none")
    assert likely.is_zero is False
    assert likely.proven is False
    assert unknown.is_zero is None


@requires_flint
def test_rigorous_ball_path_handles_abs_and_projections():
    abs_expr = sp.Abs(sp.Mul(sp.I, sp.pi, evaluate=False), evaluate=False)
    assert adaptive_precision_ball_test(abs_expr).verdict is Verdict.NONZERO_PROVEN

    re_expr = sp.re(sp.Mul(sp.Integer(3), sp.I, evaluate=False))
    im_expr = sp.im(sp.Mul(sp.Integer(3), sp.I, evaluate=False))
    assert adaptive_precision_ball_test(re_expr).is_zero is True
    assert adaptive_precision_ball_test(im_expr).verdict is Verdict.NONZERO_PROVEN


@requires_flint
def test_finite_field_identity_reports_error_bound():
    expr = sp.Add(
        sp.Pow(sp.Add(x, 1, evaluate=False), 40, evaluate=False),
        -sp.expand((x + 1) ** 40),
        evaluate=False,
    )
    result = finite_field_identity_test(
        expr, [x], target_error=1e-10, rng=random.Random(1)
    )
    assert result.suggests_zero is True
    assert result.error_bound is not None
    assert result.error_bound <= 1e-10


def test_fast_oracle_source_avoids_generic_simplification():
    import inspect

    from exprtest import core

    source = inspect.getsource(core)
    assert "sp.simplify" not in source
    assert "sp.together" not in source
    assert "sp.trigsimp" not in source


def test_public_namespace_is_intentionally_small():
    import exprtest

    expected = {
        "zerotest",
        "profile_zerotest",
        "is_prime",
        "is_integer",
        "is_rational",
        "is_real",
        "is_algebraic",
        "number_kind",
        "ElementOf",
        "Verdict",
        "ZeroClassification",
    }
    assert set(exprtest.__all__) == expected
    assert not hasattr(exprtest, "classify_zero_status")


def test_profile_exposes_classification_evidence():
    profile = profile_zerotest(sp.exp(sp.sqrt(2), evaluate=False))
    assert profile.result is False
    assert profile.classification.verdict is Verdict.NONZERO_PROVEN
    assert profile.classification.method
    assert profile.classification.evidence


def test_profile_exposes_decision_reason():
    from exprtest import profile_zerotest

    prof = profile_zerotest(sp.Integer(0))
    assert prof.result is True
    assert prof.method
    assert prof.certainty == "certified"
    assert prof.detail
    assert prof.reason.startswith(prof.method)
    assert prof.classification.certainty == prof.certainty


def test_profile_exposes_unknown_strength():
    from exprtest import profile_zerotest

    x = sp.Symbol("x")
    prof = profile_zerotest(sp.sin(x) ** 2 + sp.cos(x) ** 2 - 1)
    assert prof.result is None
    assert prof.certainty in {"heuristic", "unknown"}
    assert prof.method


def test_time_budget_propagates_callable_errors():
    def broken():
        raise RuntimeError("implementation bug")

    with pytest.raises(RuntimeError, match="implementation bug"):
        run_with_time_budget(broken, seconds=0.1, default=None)


def test_time_budget_is_safe_in_worker_threads():
    import threading

    results = []

    def worker():
        results.append(run_with_time_budget(lambda: 7, seconds=0.01, default=None))

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    assert results == [7]
