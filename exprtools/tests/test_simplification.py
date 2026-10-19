import time

import pytest
import sympy as s

from exprtools import (
    DEFAULT_REGISTRY,
    MathematicalContext,
    SimplificationBudget,
    TransformationRegistry,
    simplify,
)

B = SimplificationBudget(seconds=5)
x = s.Symbol("x")


def test_dispatcher_and_context():
    assert simplify(s.sqrt(x * x), s.Q.negative(x), budget=B) == -x
    assert simplify(s.Abs(x), context=MathematicalContext(x > 0), budget=B) == x
    # Additional assumptions are combined with the context.
    assert simplify(
        s.Abs(x), x < 0, context=MathematicalContext(x > 0), budget=B
    ) == s.Abs(x)


def test_pointwise_and_common_domain_rational_cancellation():
    e = (x * x - 1) / (x - 1)
    assert simplify(e, budget=B) == e
    assert simplify(e, s.Ne(x, 1), budget=B) == x + 1
    r = simplify(
        e, context=MathematicalContext(domain="common"), budget=B, return_result=True
    )
    assert r.expression == x + 1 and r.original == e
    assert not r.domain_preserved
    e = s.Mul(x, s.Pow(x, -1, evaluate=False), evaluate=False)
    assert simplify(e, budget=B) == e


def test_recurrences_poles_and_limit_context():
    e = s.gamma(x + 2) / s.gamma(x)
    assert simplify(e, budget=B) == e
    assert simplify(e, x > 0, budget=B) == x * x + x
    assert (
        simplify(e, context=MathematicalContext(domain="common"), budget=B) == x * x + x
    )
    t = s.Symbol("t", real=True)
    v = s.Symbol("v")
    e = s.besselj(v, t) + s.besselj(v + 2, t) - 2 * (v + 1) * s.besselj(v + 1, t) / t
    ctx = MathematicalContext(domain="germ", variables=t, target=0)
    assert simplify(e, context=ctx, budget=B) == 0
    a = s.Symbol("a")
    fixed_hole = s.Mul(a, s.Pow(a, -1, evaluate=False), evaluate=False)
    assert simplify(fixed_hole, context=ctx, budget=B) == fixed_hole
    registry = TransformationRegistry().register(
        "cancel_fixed", lambda e, c, b: s.S.One
    )
    assert simplify(fixed_hole, context=ctx, registry=registry, budget=B) == fixed_hole


def test_registry_isolation_certification_and_complexity():
    registry = TransformationRegistry().register("factor", lambda e, c, b: (x + 1) ** 2)
    assert not TransformationRegistry().transformations
    assert simplify(x * x + 2 * x + 1, registry=registry, budget=B) == (x + 1) ** 2
    assert simplify(
        s.sqrt(x * x),
        registry=TransformationRegistry().register("bad_branch", lambda e, c, b: x),
        budget=B,
    ) == s.sqrt(x * x)
    assert (
        simplify(
            x,
            registry=TransformationRegistry().register(
                "false", lambda e, c, b: s.S.Zero
            ),
            budget=B,
        )
        == x
    )
    assert (
        simplify(
            x,
            registry=TransformationRegistry().register("growth", lambda e, c, b: x + 1),
            budget=B,
        )
        == x
    )
    with pytest.raises(ValueError):
        registry.register("factor", lambda e, c, b: e)
    assert [t.name for t in DEFAULT_REGISTRY.transformations] == [
        "refine",
        "recurrences",
        "rational",
    ]


def test_registry_does_not_fill_a_hole_even_for_proven_identity():
    e = (x * x - 1) / (x - 1)
    registry = TransformationRegistry().register("cancel", lambda e, c, b: x + 1)
    assert simplify(e, registry=registry, budget=B) == e
    assert simplify(e, s.Ne(x, 1), registry=registry, budget=B) == x + 1


def test_heuristic_verdict_cannot_certify_plugin(monkeypatch):
    import importlib

    mod = importlib.import_module("exprtools.simplification")
    seen = []

    def unknown(*a, **k):
        seen.append(k["confidence"])
        return None

    monkeypatch.setattr(mod, "zerotest", unknown)
    registry = TransformationRegistry().register("factor", lambda e, c, b: (x + 1) ** 2)
    assert simplify(x * x + 2 * x + 1, registry=registry, budget=B) == x * x + 2 * x + 1
    assert seen == ["certified"]


def test_cycle_budget_growth_and_invalid_inputs():
    for budget in (
        SimplificationBudget(seconds=0),
        SimplificationBudget(max_steps=0),
        SimplificationBudget(max_ops=0),
    ):
        assert simplify(s.Abs(x), x > 0, budget=budget) == s.Abs(x)
    for kwargs in (
        {"seconds": float("nan")},
        {"seconds": -1},
        {"max_steps": 1.5},
        {"max_ops": -1},
    ):
        with pytest.raises(ValueError):
            SimplificationBudget(**kwargs)
    with pytest.raises(ValueError):
        MathematicalContext(domain="bad")
    with pytest.raises(ValueError):
        MathematicalContext(domain="germ", variables=x, target=0)
    with pytest.raises(ValueError):
        simplify(x, transformations=["missing"])
    with pytest.raises(TypeError):
        simplify(s.Matrix([x]))


def test_late_plugin_result_is_not_accepted():
    def late(e, c, b):
        time.sleep(0.01)
        return (x + 1) ** 2

    r = simplify(
        x * x + 2 * x + 1,
        registry=TransformationRegistry().register("late", late),
        budget=SimplificationBudget(seconds=0.005),
        return_result=True,
    )
    assert r.expression == r.original


def test_equal_cost_registry_cycle_is_bounded():
    a = s.Add(x, 1, evaluate=False)
    b = s.Add(1, x, evaluate=False)
    registry = (
        TransformationRegistry()
        .register("reverse", lambda e, c, k: b)
        .register("restore", lambda e, c, k: a)
    )
    r = simplify(
        a, registry=registry, budget=B, measure=lambda e: 0, return_result=True
    )
    assert r.steps <= 1


def test_compact_coefficient_expansion_is_refused():
    e = (x + 1) ** 10000 / (x + 2)
    assert simplify(e, budget=B) == e
    a = s.symbols("a:24")
    e = s.prod(a[2 * j] + a[2 * j + 1] for j in range(12))
    assert simplify(e, budget=B) == e
