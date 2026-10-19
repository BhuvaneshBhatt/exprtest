"""Bounded simplification dispatcher and immutable transformation registry."""

from dataclasses import dataclass
from typing import Callable

import sympy as sp

from ._result import Verdict
from ._simplification_models import SimplificationBudget, SimplificationResult, _Run
from ._structural_gap import structural_algebraic_test
from .context import is_defined, resolve_context
from .core import zerotest
from .evidence import TransformationEvidence
from .recurrence import simplify_recurrences
from .refinement import refine


@dataclass(frozen=True)
class Transformation:
    name: str
    apply: Callable

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name or not callable(self.apply):
            raise TypeError("transformations need a nonempty name and callable")


@dataclass(frozen=True)
class TransformationRegistry:
    """Per-caller ordered registry; register returns a new registry.

    Callbacks receive (expression, context, remaining_budget), and return an
    expression. Third-party proposals require certified zero testing as well as
    definedness proofs in pointwise mode. Plugin code is trusted to terminate.
    """

    transformations: tuple[Transformation, ...] = ()

    def __post_init__(self):
        entries = tuple(self.transformations)
        if any(not isinstance(t, Transformation) for t in entries):
            raise TypeError("registry entries must be Transformations")
        if len({t.name for t in entries}) != len(entries):
            raise ValueError("duplicate transformation name")
        object.__setattr__(self, "transformations", entries)

    def register(self, name, apply):
        return TransformationRegistry(
            (*self.transformations, Transformation(name, apply))
        )


def _refinement(expr, context, budget):
    return refine(expr, context=context, budget=budget, return_result=True)


def _recurrence(expr, context, budget):
    return simplify_recurrences(
        expr,
        assumptions=context.recurrence_assumptions,
        variables=context.variables if context.domain == "germ" else (),
        target=context.target if context.domain == "germ" else (),
        max_steps=budget.max_steps,
        max_ops=budget.max_ops,
        budget_seconds=budget.seconds,
        require_defined_germ=context.domain == "germ",
        return_result=True,
    )


def _rational(expr, context, budget):
    # count_ops alone misses compact powers and products whose cancellation
    # would expand exponentially. Bound coefficient work before entering CAS.
    def expansion_size(node):
        if node.is_Add:
            return min(257, sum(expansion_size(a) for a in node.args))
        if node.is_Mul:
            size = 1
            for arg in node.args:
                size *= expansion_size(arg)
                if size > 256:
                    return 257
            return size
        if node.is_Pow and node.exp.is_Integer:
            if abs(node.exp) > 8:
                return 257
            return min(257, expansion_size(node.base) ** abs(int(node.exp)))
        return 1

    if expansion_size(expr) > 256:
        return expr
    symbols = tuple(sorted(expr.free_symbols, key=sp.default_sort_key))
    if symbols and expr.is_rational_function(*symbols):
        return sp.cancel(expr)
    return expr


def _algebraic(expr, context, budget):
    if expr.free_symbols or not expr.has(sp.Pow):
        return expr
    return (
        sp.S.Zero
        if structural_algebraic_test(expr).verdict is Verdict.ZERO_PROVEN
        else expr
    )


DEFAULT_REGISTRY = TransformationRegistry(
    (
        Transformation("refine", _refinement),
        Transformation("recurrences", _recurrence),
        Transformation("algebraic", _algebraic),
        Transformation("rational", _rational),
    )
)


def simplify(
    expr,
    assumptions=True,
    *,
    context=None,
    registry=None,
    transformations=None,
    budget=None,
    measure=sp.count_ops,
    return_result=False,
):
    """Select no-more-complex certified proposals within explicit domain policy.

    Default pointwise mode refuses cancellation of unresolved singularities.
    Common-domain mode retains the original domain in the result. Recurrence
    adapters remain available through the lower-level recurrence API.
    A budget is cooperative: it cannot preempt an arbitrary plugin/SymPy call.
    """
    original = sp.sympify(expr)
    if not isinstance(original, sp.Expr) or original.is_Matrix:
        raise TypeError("simplify expects a scalar expression")
    context = resolve_context(context, assumptions)
    budget = SimplificationBudget() if budget is None else budget
    registry = DEFAULT_REGISTRY if registry is None else registry
    if not isinstance(budget, SimplificationBudget) or not isinstance(
        registry, TransformationRegistry
    ):
        raise TypeError("invalid simplification budget or registry")
    selected = registry.transformations
    if transformations is not None:
        names = (
            (transformations,)
            if isinstance(transformations, str)
            else tuple(transformations)
        )
        by_name = {t.name: t for t in selected}
        if any(n not in by_name for n in names):
            raise ValueError("unknown transformation")
        selected = tuple(by_name[n] for n in names)
    run = _Run(budget)
    current = original
    seen = {current}

    def finish():
        result = SimplificationResult(
            original,
            current,
            tuple(run.evidence),
            run.steps,
            run.stopped,
            context.domain,
        )
        return result if return_result else current

    if sp.count_ops(original) > budget.max_ops:
        run.stopped = "input operation cap"
        return finish()
    if not run.available():
        return finish()
    if not context.consistent:
        run.stopped = "inconsistent assumptions"
        return finish()
    while run.available():
        changed = False
        for transformation in selected:
            if not run.available():
                break
            proposal = transformation.apply(current, context, run.remaining())
            trusted = any(
                transformation.apply is f
                for f in (_refinement, _recurrence, _algebraic, _rational)
            )
            if trusted and any(
                transformation.apply is f for f in (_refinement, _recurrence)
            ):
                candidate = proposal.expression
                evidence = proposal.evidence
                steps = max(1, proposal.steps)
            else:
                candidate = sp.sympify(proposal)
                evidence = ()
                steps = 1
            if not isinstance(candidate, sp.Expr) or candidate.is_Matrix:
                raise TypeError("transformation must return a scalar expression")
            if candidate == current or candidate in seen:
                continue
            if sp.count_ops(candidate) > budget.max_ops:
                continue
            if measure(candidate) > measure(current):
                continue
            if transformation.apply is not _refinement and (
                context.domain == "pointwise"
                or (
                    context.domain == "germ" and transformation.apply is not _recurrence
                )
            ):
                if not is_defined(current, context) or not is_defined(
                    candidate, context
                ):
                    continue
            if not trusted:
                if (
                    zerotest(
                        current - candidate,
                        assumptions=context.assumptions,
                        use_cache=True,
                        confidence="certified",
                    )
                    is not True
                ):
                    continue
            # Never accept a plugin proposal returned after its time budget.
            if not run.available() or run.steps + steps > budget.max_steps:
                continue
            current = candidate
            seen.add(current)
            changed = True
            run.steps += steps
            run.evidence.extend(
                evidence
                or (
                    TransformationEvidence(
                        transformation.name,
                        "Certified scalar identity; domain policy: " + context.domain,
                        (),
                        candidate,
                    ),
                )
            )
        if not changed:
            break
    return finish()
