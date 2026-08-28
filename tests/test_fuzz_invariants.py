"""Small deterministic fuzz checks for robustness and representation invariants."""

import random

import sympy as sp

from exprtest import zerotest


def _leaf(rng, x, y):
    return rng.choice(
        [x, y, sp.Integer(rng.randint(-3, 3)), sp.sqrt(rng.choice([2, 3, 5]))]
    )


def _tree(rng, x, y, depth):
    if depth <= 0:
        return _leaf(rng, x, y)
    op = rng.choice(["add", "mul", "square"])
    if op == "add":
        return sp.Add(
            _tree(rng, x, y, depth - 1), _tree(rng, x, y, depth - 1), evaluate=False
        )
    if op == "mul":
        return sp.Mul(
            _tree(rng, x, y, depth - 1), _tree(rng, x, y, depth - 1), evaluate=False
        )
    return sp.Pow(_tree(rng, x, y, depth - 1), 2, evaluate=False)


def test_bounded_generated_expressions_never_escape_and_cache_agrees():
    rng = random.Random(314159)
    x, y = sp.symbols("x y")
    for _ in range(40):
        expr = _tree(rng, x, y, 2)
        uncached = zerotest(expr, seed=9, use_cache=False)
        cached = zerotest(expr, seed=9, use_cache=True)
        assert cached == uncached


def test_srepr_round_trip_preserves_classification_for_generated_exact_trees():
    rng = random.Random(271828)
    x, y = sp.symbols("x y")
    namespace = vars(sp).copy()
    namespace.update({"x": x, "y": y})
    for _ in range(20):
        expr = _tree(rng, x, y, 2)
        rebuilt = eval(sp.srepr(expr), {"__builtins__": {}}, namespace)
        assert zerotest(expr, seed=3, use_cache=False) == zerotest(
            rebuilt, seed=3, use_cache=False
        )
