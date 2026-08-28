# Performance design

`zerotest()` is organized around predictable admission rules rather than broad
symbolic simplification. The normal fast path does not call generic
`simplify()`, `trigsimp()`, or an unrestricted symbolic expander.

Key mechanisms are:

- cached one-pass expression features for routing and cost estimates;
- cheap arithmetic, assumptions, and structural nonzero checks first;
- method-specific operation, node, term, degree, and bit-size gates;
- call-local memoization only above a size threshold;
- bounded sparse algebraic towers before more general number-field work;
- layered algebraic separation bounds;
- rigorous Arb precision chosen from structural/separation hints;
- bounded result, normal-form, exact-object, theorem, and negative-applicability caches.

## Current implementation budgets

These values are implementation limits, not API guarantees. They can change as
algorithms improve.

| Area | Current limit |
| --- | ---: |
| Generic exact oracle | 160 ops / 320 nodes / depth 28 |
| Exact algebraic generators | 8 fast-path generators |
| Fast algebraic degree product | 256 |
| Tower stage | 100 ops / 6 generators / 80 ms sign budget |
| Cyclotomic order | 1024 fast-path maximum |
| Log terms | 12 |
| PSLQ terms | 8 |
| PSLQ precision | 90 decimal digits |
| Exponential-independence terms | 6 |
| Algebraic exponent-gap fallback | <=48 ops / 30 ms |
| Square-root sum | 12 terms |
| Square-root radicand | 32-bit positive integer |
| Quadratic denesting pre-pass | 24 ops |
| Rational identity normalizer | 64 ops / 128 nodes / 6 variables |
| Elementary identity normalizer | 80 ops / 160 nodes |
| Final result cache | 2048 entries |
| Negative applicability cache | 2048 entries |

The source of truth is `src/exprtest/_config.py`.

## Performance tests versus benchmarks

Correctness tests include a small `performance_contract` suite. These tests do
not assert microsecond-level latency. Instead they verify stable architectural
properties: oversized stages refuse quickly, negative-applicability checks stay
cheap, and bounded methods do not accidentally broaden into expensive general
symbolic work. Their time ceilings are deliberately generous for shared CI
hosts.

Actual latency measurement lives in `benchmarks/benchmark_zerotest.py`. CI
stores benchmark output as an artifact rather than making machine-dependent
microsecond numbers a release gate.

## Reference latency

On the FLINT-enabled Python 3.13 Linux x86-64 environment used for the theorem
fast-path pass, three consecutive 5,000-case runs produced cold medians of
28.4, 30.7, and 27.7 microseconds; the repeated-result median was 8.6
microseconds in all three runs. A later validation run measured about 28.0
microseconds cold and 8.6 microseconds repeated.

These numbers are comparison baselines only. Hardware, Python, SymPy, allocator
state, and optional backends all affect wall-clock results.

## Why the specialized fast paths are bounded

The exponent-distinctness fallback first uses tiny structural reasoning, then a
square-root basis proof when applicable, and only then admits algebraic gap
construction below its operation/time limits. Square-root sums cap both term
count and radicand size so prime factorization cannot become unbounded. The
quadratic denester recognizes only a narrow exact shape before the general
algebraic machinery.

Negative-applicability caches ensure that expressions with no relevant
structure do not repeatedly pay even the setup cost of these stages.
