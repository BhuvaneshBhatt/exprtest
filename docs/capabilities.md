# Capabilities

The table below describes the bounded public oracle. `profile_zerotest()` runs
the same oracle without relying on the final-result cache and records stage
timings; it is diagnostic instrumentation, not a separate slower solver.

| Expression class | Zero proof | Nonzero proof | Main method |
| --- | --- | --- | --- |
| Exact integers and rationals | Yes | Yes | exact arithmetic |
| Bounded polynomial/rational identities | Yes | Yes | exact cancellation/normal form |
| Small exact algebraic constants | Yes | Yes | towers / exact algebraic reduction |
| Rational sums of small positive-integer square roots | Yes | Yes | squarefree radical basis |
| Nested radicals within tower budgets | Yes | Yes when certified | sparse algebraic tower |
| Roots of unity and rational-angle trig constants | Yes | Yes | cyclotomic/exact trig reduction |
| Rational logarithmic relations | Yes | Yes | prime-exponent vectors |
| Selected positive algebraic log relations | Yes | Yes | exact multiplicative relation |
| Small algebraic linear combinations of exponentials | Limited | Yes | exponential independence + exponent separation |
| Algebraic-base powers with algebraic irrational exponent | N/A | Yes against algebraic values | Gelfond--Schneider classification |
| Selected exact special-function values | Yes | Yes | reviewed exact rules |
| Rigorous Arb/Acb evaluation | Exact enclosure only | Yes when zero is excluded | ball arithmetic |
| Rational functions with free symbols | Some exact identities | Yes in supported cases | exact normalization / finite field |
| Generic symbolic identities | Limited | Limited | usually `None` |

## Reviewed function facts

A small Python-native registry supplements SymPy's assumptions with reviewed,
cheap facts for 20 common functions. It contributes selected definedness,
integer, real, and sign properties for calls such as `Abs`, `log`, inverse
trigonometric functions, hyperbolic functions, `erf`/`erfc`, `gamma`,
`factorial`, `floor`, `ceiling`, `loggamma`, and `zeta`.

The executable rules are intentionally narrower than a general function
knowledge base. See [function_facts.md](function_facts.md) for the exact current
inventory and [assumptions.md](assumptions.md) for how prerequisites are proved.

## Exact theorem fast paths

Several specialized methods exist specifically to avoid invoking a more general
algebraic or numerical engine:

- branch-safe exp/log normalization, including integer `2*pi*I` periodicity;
- rational-log prime factorization and positive-algebraic log relations;
- exponential independence with certified algebraic exponent separation;
- Gelfond--Schneider recognition for a narrow power shape;
- squarefree-basis testing for bounded sums of square roots;
- a small quadratic nested-radical denesting pre-pass.

All are deliberately incomplete and structurally gated.
