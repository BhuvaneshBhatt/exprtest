# Soundness model

The default public contract is deliberately conservative:

- `True`: the expression is proved to be zero.
- `False`: the expression is proved to be nonzero.
- `None`: no certified conclusion was obtained within the bounded oracle.

A false proof is considered substantially worse than an inconclusive result.
The implementation therefore refuses transformations around uncertain domains,
complex branches, dependent algebraic generators, and unsupported
transcendence questions.

## Certified conclusions

Proof-producing methods include exact arithmetic, bounded exact identities,
algebraic reductions, cyclotomic arithmetic, squarefree-radical basis
reduction, theorem-based transcendence/independence, certified algebraic
separation, and rigorous Arb/Acb enclosures that either collapse to exact zero
or exclude zero.

PSLQ is candidate generation only. A proposed relation must pass an independent
exact verifier before it can produce `ZERO_PROVEN`.

## Non-proof evidence

`NONZERO_LIKELY` records a concrete one-sided witness that is useful but not a
certified universal conclusion. `ZERO_UNPROVEN` records zero-like evidence that
is not strong enough to prove an identity. Under the default
`confidence="certified"` policy both map to `None`; the default
`confidence="probable"` policy can additionally map only `NONZERO_LIKELY` to `False`.

## Branch and domain safety

Logarithm, power, inverse-function, and complex rewrites fire only when their
preconditions are proved. Definedness is tracked separately from sign and
reality. A fact that a function would be real *if defined* is not evidence that
its argument is away from a pole or excluded point. Branch cuts are likewise
not treated as poles.

## Floating and rigorous numeric inputs

A finite SymPy `Float` literal is classified by its stored value: a stored zero
is zero, while a stored nonzero value such as `1e-11` is nonzero. This rule does
not turn approximate cancellation in a compound expression into an exact
identity proof.

Arb/Acb values are enclosures rather than ordinary point estimates. An
enclosure excluding zero proves nonzero. A non-degenerate enclosure containing
zero is inconclusive unless it is known to represent exact zero.

## Specialized theorem safety

Exponential independence is used only after the coefficients and exponents
meet the required algebraic hypotheses and pairwise exponent distinctness is
certified. Gelfond--Schneider is used only after the base is cheaply proved
algebraic and different from zero and one, and the exponent is cheaply proved
algebraic irrational.

For bounded `sum(q_i*sqrt(n_i))` expressions, positive integer radicands are
reduced to squarefree classes. Linear independence of distinct squarefree
radicals over the rationals then gives both zero and nonzero certificates. The
method refuses unsupported radicands or term counts rather than falling through
to unsafe assumptions.
