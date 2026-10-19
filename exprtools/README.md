# exprtools

Expression predicates, guarded recurrence reduction, assumption-aware refinement,
and a bounded simplification dispatcher for SymPy scalar expressions. This is an
independent distribution housed in the exprtest repository. Python >=3.10,
SymPy >=1.12 and mpmath >=1.3 are required; python-flint is optional.

```sh
# From the repository root:
pip install -e './exprtools[test,flint]' -e .
pytest
```

The root project builds `exprtest` 0.2, a compatibility distribution depending
on `exprtools` 0.1. Install `exprtools` alone if old imports are unnecessary.
The two wheels own disjoint import directories. Existing public predicates,
private submodule imports, mutable caches/configuration, and historical pickle
paths through exprtest resolve to the same implementations and types.

## Predicate API

```python
from exprtools import zerotest, profile_zerotest, is_real, number_kind
```

All predicate APIs and algorithms from exprtest 0.1 are preserved, including
`ElementOf`, `Verdict`, `ZeroClassification`, `is_algebraic`, `is_integer`,
`is_prime`, and `is_rational`. The probable confidence default is unchanged.
Only `confidence="certified"` may certify a third-party simplification proposal.
Numerical proximity to zero is never enough to accept one.

## Refine and simplify

```python
import sympy as s
from exprtools import (
    MathematicalContext, SimplificationBudget, refine, simplify,
    TransformationRegistry,
)
x = s.Symbol('x')
assert refine(s.sqrt(x**2), s.Q.negative(x)) == -x
assert refine(s.log(s.exp(x)), s.Q.real(x)) == x
assert simplify(s.Abs(x), x > 0) == x

expression = (x**2-1)/(x-1)
assert simplify(expression) == expression  # unresolved singularity at x=1
assert simplify(expression, s.Ne(x,1)) == x+1
result = simplify(expression,
    context=MathematicalContext(domain='common'), return_result=True)
assert result.expression == x+1
assert result.original == expression
assert not result.domain_preserved
```

`refine(expr, assumptions=True, *, context=None, budget=None,
return_result=False)` uses its **own rewrite implementation**, with SymPy's
predicate prover and bounded rational linear implication checks. It does not
call SymPy refine or its handlers. Supported rules cover absolute values,
real even roots, parity, sign/argument, real/imaginary/conjugate components,
integer floor/ceiling, integer multiples of pi, exp/log inverses with proved
conditions, and positive-base logarithmic powers. Piecewise branches use their
condition and the negations of all preceding conditions. Bound-variable
constructs (integrals, sums, lambdas, derivatives, limits, substitutions) remain
opaque to avoid variable capture and assumptions leaking across scopes.

Explicit assumptions combine with an optional context; global SymPy assumptions
are excluded. Recognized contradictions return the input unchanged with
`stopped="inconsistent assumptions"`. Assumption reasoning is conservative,
not a complete satisfiability solver. Unknown conditions leave the relevant
subexpression unchanged. Complex powers are not split; logarithms of complex
powers and unknown sqrt-square branches are not forced.

`simplify` tries `refine`, `recurrences`, and `rational` in that order, retaining
no-more-complex results. `transformations=(...)` selects named stages. A caller
can supply `measure`, an immutable registry, and an explicit mathematical context.

- `domain="pointwise"` (default) preserves definedness throughout the context.
  Non-refinement proposals require conservative definedness checks for both
  expressions; opaque functions and unresolved denominators are refused.
- `domain="common"` admits identities on the original common function domain.
  The result retains the original expression and does not certify an extension
  to removed poles. Use `return_result=True` when retaining this obligation.
- `domain="germ"` supplies one intrinsically real symbol and an extended real
  target to the recurrence engine's existing punctured-neighborhood guards.
  It retains the original expression and its domain obligations.

Symbols represent finite complex scalar variables unless assumptions restrict
them. The framework is deliberately conservative about unsupported function
singularities. It is not a complete CAS simplifier or domain solver.

## Registry and resource budgets

```python
registry = TransformationRegistry().register(
    'factor', lambda expr, context, budget: s.factor(expr))
assert simplify(x*x + 2*x + 1, registry=registry) == (x+1)**2
```

Callbacks return scalar expression proposals. The dispatcher checks the operation
cap, complexity measure, and domain policy, then requires a certified zero-test
identity for third-party proposals. The original expression is retained in every
structured result. Registry instances never mutate global state; duplicate names
are rejected. Plugins are trusted Python code and must terminate cooperatively.

`SimplificationBudget(max_steps=24, max_ops=240, seconds=0.25)` bounds accepted
rewrite steps, expression size, and elapsed time between operations. Budgets
cannot preempt an individual SymPy or plugin operation. A late proposal is
refused. Results expose `original`, `expression`, `evidence`, `steps`, `stopped`,
`domain`, and `domain_preserved`; stopping is not a proof of impossibility.

## Recurrence API and host adapters

```python
from exprtools import simplify_recurrences, RecurrenceFamilies
```

The original recurrence keywords, limits and mathematical guards are preserved.
The lower-level function retains **meromorphic/common-domain** semantics and is
not the dispatcher's pointwise default. It adds `families=` and `record_event=`.
Evidence uses `TransformationEvidence(method, statement, substitutions, value)`.

`RecurrenceFamilies()` contains native SymPy families. External packages bind
actual function classes to named mathematical conventions such as
`RecurrenceFamilies(ParabolicCylinderD=MyCylinderD)`. Class names are never used
as evidence of a mathematical convention. Unbound roles are unavailable.
Providers may subclass `EXTRA_HEADS`, `TWO_BASIS`, `signatures`, `function_at`, and
`next_basis`; every introduced denominator must pass the supplied `guard`.
Adapters are responsible for supplying functions with those exact conventions.

The asymptotic repository binds its existing special-function classes per call,
converts evidence into its existing `LimitEvidence` and forwards instrumentation.
No exprtools module imports asymptotic. Limit-only fallback policies remain there.

## Validation and release order

The repository's `docs/exprtools-migration/` records baseline commits, coverage,
benchmarks and stage results. The root tests exercise all legacy predicate APIs;
`exprtools/tests/` adds the framework, independence and soundness regressions.
Build this distribution with `python -m build exprtools --outdir dist`, then
build the compatibility package at the repository root. Release exprtools before
exprtest 0.2 and asymptotic 0.2.2, which depend on its availability. The existing
exprtest publication workflow still targets the compatibility distribution;
configure a separate trusted publisher for exprtools before releasing it.
