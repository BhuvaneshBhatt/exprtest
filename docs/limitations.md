# Limitations

The principal limitation is intentional: `exprtest` is a bounded proof oracle,
not a complete symbolic simplifier or decision procedure.

## Free-variable identities

General symbolic identities can still return `None` when they fall outside the
bounded polynomial/rational and elementary normalizers.

```python
from sympy import Function, symbols
from exprtest import zerotest

x = symbols("x")
f = Function("f")
zerotest(f(x))
# None
```

## Algebraic degree growth

Many independent algebraic generators can create extension degrees that grow
multiplicatively. The package uses sparse towers, dependency-aware modeling,
and degree limits, then stops before uncontrolled primitive-element or
resultant growth. Expressions beyond those gates may therefore be
mathematically decidable but return `None` here.

## Complex branches

Principal logarithms, powers, square roots, and inverse functions are not
rewritten through identities whose branch conditions are unknown. For example,
without a positivity/realness assumption the package does not assume
`sqrt(x**2) == x`.

## Transcendental combinations

The implemented transcendence theorems cover named structural cases rather
than arbitrary combinations. Relations involving several unrelated
transcendental constants can remain unknown even when strong numerical evidence
exists.

## Function knowledge

The function-fact registry contains 20 reviewed SymPy functions, not a general
special-function theorem database. Detailed global ranges, extrema, monotonicity,
convexity, branch geometry, and many singularity descriptions are not modeled.
The exact inventory is in [function_facts.md](function_facts.md).

## Rigorous numeric backend

Arb/Acb support requires the optional `python-flint` dependency:

```bash
pip install "exprtest[flint]"
```

Without it, stages requiring rigorous ball arithmetic remain inconclusive; the
package does not silently substitute ordinary floating-point approximation as a
certificate.

## Bounded methods can refuse valid inputs

Fast paths deliberately have structural limits. Examples include the number of
square-root terms, radicand bit size, algebraic generator/degree limits,
cyclotomic order, and PSLQ dimension. Crossing a limit means “use another
admitted stage or return `None`,” not “the expression is nonzero.” Current
implementation limits are summarized in [performance.md](performance.md).
