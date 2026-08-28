# Architecture

`exprtest` is a bounded proof cascade. The public oracle tries cheap, highly
applicable methods first and admits more specialized or expensive methods only
when structural metadata says they are relevant.

```text
input
  |
  +-- literal arithmetic / direct refinement
  |
  +-- definedness and assumption facts
  |
  +-- bounded polynomial, rational, and elementary identities
  |
  +-- exact local rewrites and selected special values
  |
  +-- cheap structural nonzero and number-kind theorems
  |
  +-- exp/log normalization and transcendence relations
  |
  +-- cyclotomic and square-root-sum methods
  |
  +-- bounded algebraic towers and exact algebraic reduction
  |
  +-- verified PSLQ candidates
  |
  +-- rigorous Arb/Acb separation when available
  |
  +-- free-variable witness / finite-field stages
  |
  `-- None when the admitted methods are inconclusive
```

The exact ordering differs slightly between closed constants and expressions
with free symbols. `profile_zerotest()` records the actual stages used for one
call and is the best way to inspect routing.

## Classification layers

The internal `ZeroClassification` has five verdicts:

| Verdict | Meaning | Public certified policy |
| --- | --- | --- |
| `ZERO_PROVEN` | exact or rigorous proof of zero | `True` |
| `NONZERO_PROVEN` | exact or rigorous proof of nonzero | `False` |
| `NONZERO_LIKELY` | one-sided witness evidence | `None` |
| `ZERO_UNPROVEN` | zero-like evidence without proof | `None` |
| `UNKNOWN` | no useful conclusion | `None` |

The default `confidence="probable"` additionally maps `NONZERO_LIKELY` to `False`; `confidence="certified"` leaves it as `None`.
It never promotes `ZERO_UNPROVEN` to `True`.

## Applicability gates

Each expensive or specialized stage should have a cheap refusal path. Routing
uses cached expression features, operation/node budgets, method-specific term
limits, and bounded timeouts where portable interruption is available. The
negative-applicability cache stores only deterministic facts such as “this
expression has no logarithm structure”; it never caches a mathematical
`UNKNOWN` as if it were a proof.

## Proof stages and evidence stages

Exact arithmetic, bounded identities, algebraic reduction, cyclotomic
arithmetic, square-root basis reduction, theorem-based transcendence,
certified separation bounds, verified PSLQ relations, and rigorous interval
separation can produce certified conclusions.

Random numerical witnesses and some finite-field outcomes can produce
one-sided evidence. Candidate generation is never itself a proof: PSLQ, for
example, must be followed by an independent exact verifier before the oracle
returns `True`.

## Caches

The package separates caches by purpose:

- final-result cache: stores proof-grade classifications only;
- structural caches: expression features, nonzero facts, and normal forms;
- exact-object caches: reusable algebraic/minimal-polynomial data;
- theorem caches: exponent-separation and squarefree-radical work;
- negative-applicability caches: deterministic stage refusal decisions.

Global cache clearing resets all of these categories.

## Design rule for new methods

A new method belongs on the fast path only when it has a clear mathematical
contract and a predictable cost envelope. See [development.md](development.md)
for the contributor checklist.
