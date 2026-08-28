# Assumptions and definedness

Caller assumptions are normalized before classification. Direct equality
substitutions are applied when structurally safe, and SymPy's assumptions
system is queried conservatively for inexpensive predicates.

Equivalent assumption forms can arrive through symbol properties, relational
conditions such as `x > 0`, or predicates such as `Q.positive(x)`. A rule fires
only when its prerequisite is actually proved; an undecidable prerequisite
propagates as `None` rather than being guessed.

## Definedness is separate

Before using a sign fact to prove nonzero, the relevant expression must be
known to be defined. This matters for logarithms, tangent/hyperbolic tangent,
gamma-family poles, factorial poles, and zeta at its pole. Branch cuts are not
interchangeable with poles or undefined points.

## Branch-sensitive identities

Logarithm and power transformations require the necessary positivity,
realness, nonvanishing, integrality, or principal-branch conditions. When those
conditions cannot be established cheaply, the transformation is refused.

## Function-fact registry

The reviewed registry is implemented directly against SymPy functions. Its
conditions are small combinations of cheap predicates such as positivity,
nonnegativity, integrality, real-valuedness, and nonzeroness. It invokes neither
`solve()` nor general simplification.

The registry is tested table-wise: every registered function has domain or
property coverage, an edge/exception case, and a refusal case. See
[function_facts.md](function_facts.md).

## Random and finite-field witnesses

Random witness points are accepted only when supplied assumptions hold.
Generic finite-field sampling is skipped for constrained domains that may form
a proper algebraic subvariety, because unconstrained modular samples would not
be valid witnesses for that domain.
