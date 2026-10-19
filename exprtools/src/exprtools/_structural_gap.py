"""Exact structural separation bounds followed by rigorous Acb certification.

Inspired by the algebraic-integer numerator/denominator technique evaluated in
rred.txt. Integer ceilings replace logarithmic floating-point estimates. No
minimal polynomial, factorization, or general number field is constructed.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import sympy as sp

from . import _config as cfg
from ._features import expression_features
from ._result import Verdict, ZeroClassification


@dataclass(frozen=True)
class StructuralSeparationBound:
    """Conditional bound: value != 0 implies |value| >= 2**(-bits).

    A positive bound is NOT a nonzero certificate. ``degree`` bounds the field
    degree; ``numerator_bits`` and ``denominator_bits`` bound all conjugates of
    an algebraic-integer numerator and a positive integer denominator.
    """

    bits: int
    degree: int
    numerator_bits: int
    denominator_bits: int

    @property
    def lower(self):
        return sp.Rational(1, 1 << self.bits)


def _admitted(expr):
    f = expression_features(expr)
    if (
        expr.free_symbols
        or f.has_float
        or f.has_nonfinite
        or f.ops > cfg.STRUCTURAL_GAP_MAX_OPS
        or f.nodes > cfg.STRUCTURAL_GAP_MAX_NODES
        or f.depth > cfg.EXACT_MAX_DEPTH
        or f.max_int_bits > cfg.EXACT_MAX_INT_BITS
    ):
        return False
    return all(
        max(abs(int(r.p)).bit_length(), int(r.q).bit_length()) <= cfg.EXACT_MAX_INT_BITS
        for r in expr.atoms(sp.Rational)
    )


@lru_cache(maxsize=cfg.EXACT_BOUND_CACHE_SIZE)
def _bound_cached(expr, max_degree, max_bits, max_root, max_power):
    memo = {}
    generators = set()
    degree = 1

    def walk(node):
        nonlocal degree
        if node in memo:
            return memo[node]
        if node.is_Rational:
            numerator = abs(int(node.p))
            result = (
                0 if numerator <= 1 else (numerator - 1).bit_length(),
                (int(node.q) - 1).bit_length(),
            )
        elif node is sp.I:
            if node not in generators:
                generators.add(node)
                degree *= 2
            result = (0, 0)
        elif node.is_Add or node.is_Mul:
            parts = [walk(a) for a in node.args]
            if any(p is None for p in parts):
                return None
            u, den_bits = parts[0]
            for v, m in parts[1:]:
                u, den_bits = (
                    (max(u + m, v + den_bits) + 1, den_bits + m)
                    if node.is_Add
                    else (u + v, den_bits + m)
                )
                if max(u, den_bits) > max_bits:
                    return None
            result = (u, den_bits)
        elif node.is_Pow and node.exp.is_Rational:
            p, q = int(node.exp.p), int(node.exp.q)
            if p < 0 or p > max_power or q > max_root:
                return None
            parts = walk(node.base)
            if parts is None:
                return None
            u, den_bits = parts
            if q > 1:
                key = (node.base, q)
                if key not in generators:
                    generators.add(key)
                    degree *= q
                # If alpha=B/C, beta=alpha**(1/q)=(B*C**(q-1))**(1/q)/C.
                # C is a positive integer, so principal branches are preserved.
                u = (u + (q - 1) * den_bits + q - 1) // q
            result = (p * u, p * den_bits)
        else:
            return None
        if degree > max_degree or max(result) > max_bits:
            return None
        memo[node] = result
        return result

    result = walk(expr)
    if result is None:
        return None
    u, den_bits = result
    bits = (degree - 1) * u + den_bits
    return (
        StructuralSeparationBound(bits, degree, u, den_bits)
        if bits <= max_bits
        else None
    )


def structural_separation_bound(expr):
    """Return a conditional exact gap for bounded closed radical arithmetic.

    Supports rationals, I, sums/products, and nonnegative rational powers.
    Reciprocals, free symbols, functions, root objects, inexact and nonfinite
    values are refused. Unknown/potentially zero denominators are never erased.
    Distinct radical DAG nodes contribute their indices once to a degree bound.
    """
    expr = sp.sympify(expr)
    if not isinstance(expr, sp.Expr) or not _admitted(expr):
        return None
    return _bound_cached(
        expr,
        cfg.STRUCTURAL_GAP_MAX_DEGREE,
        cfg.STRUCTURAL_GAP_MAX_BITS,
        cfg.STRUCTURAL_GAP_MAX_ROOT,
        cfg.STRUCTURAL_GAP_MAX_POWER,
    )


def structural_algebraic_test(expr):
    """Certify zero only when a rigorous absolute enclosure is below the gap."""
    from . import _numeric as numeric

    expr = sp.sympify(expr)
    bound = structural_separation_bound(expr)
    unknown = ZeroClassification(
        Verdict.UNKNOWN,
        "algebraic-structural",
        detail="unsupported structure or separation budget",
    )
    if bound is None or numeric.flint is None:
        return unknown
    precision = cfg.INITIAL_PREC_BITS
    history = []
    limit = min(cfg.MAX_PREC_BITS, cfg.STRUCTURAL_GAP_MAX_PREC)
    while precision <= limit:
        try:
            with numeric._flint_precision(precision):
                value = numeric._sympy_to_acb_ball(expr, precision, {})
                if not value.is_finite:
                    return unknown
                history.append(f"{precision} bits: {value}")
                if 0 not in value:
                    return ZeroClassification(
                        Verdict.NONZERO_PROVEN,
                        "algebraic-structural",
                        detail="Acb enclosure rigorously excludes zero",
                        precision_bits=precision,
                        evidence="rigorous-enclosure",
                        enclosure_history=tuple(history),
                    )
                # The entire complex absolute enclosure, not only its radius
                # or midpoint, must be strictly below the conditional lower bound.
                if abs(value) < numeric.flint.arb(2) ** (-bound.bits):
                    return ZeroClassification(
                        Verdict.ZERO_PROVEN,
                        "algebraic-structural",
                        detail=f"absolute enclosure below 2**(-{bound.bits}); field degree <= {bound.degree}",
                        precision_bits=precision,
                        evidence="structural-separation-and-enclosure",
                        enclosure_history=tuple(history),
                    )
        except (
            numeric.UnsupportedNode,
            ValueError,
            TypeError,
            OverflowError,
            ZeroDivisionError,
        ):
            return unknown
        if precision >= limit:
            break
        precision = min(limit, max(2 * precision, bound.bits + cfg.GUARD_BITS))
    return unknown


def clear_structural_cache():
    _bound_cached.cache_clear()
