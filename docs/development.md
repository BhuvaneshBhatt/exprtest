# Development

Install the package in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
pytest
```

Run the benchmark separately:

```bash
python benchmarks/benchmark_zerotest.py
```

## Test organization

The suite is organized by responsibility rather than by implementation history:

- `test_contract_matrix.py`: public Boolean/verdict/certainty semantics;
- `test_metamorphic.py`: transformations that must preserve certified answers;
- `test_differential_exact.py`: specialized exact stages cross-checked against independent exact methods;
- `test_boundaries_and_caches.py`: method limits, refusal behavior, and cache clearing;
- `test_assumption_equivalence.py`: equivalent and contradictory assumptions;
- `test_function_facts.py`: table-driven reviewed function facts;
- `test_fuzz_invariants.py`: deterministic bounded generated-expression invariants;
- `test_performance_contract.py`: generous structural latency/refusal contracts;
- `test_release_gate.py`: adversarial soundness regressions;
- existing algebraic, transcendental, domain, routing, and oracle modules cover their named subsystems.

Tests should prefer observable behavior or pure helper contracts over runtime
patching. Randomized tests must use fixed seeds and small bounded generators.

## Adding a proof method

A new fast-path method should satisfy all of the following before it is routed
from `zerotest()`:

1. **Mathematical contract.** State exactly what hypotheses permit a zero or
   nonzero certificate and what unsupported inputs return.
2. **Cheap applicability gate.** Reject irrelevant expressions before doing
   expensive algebra, factorization, numerical evaluation, or traversal beyond
   the method's intended scale.
3. **Explicit budget.** Put term/operation/degree/bit/precision limits in
   `_config.py` when the cost can grow materially.
4. **Three-valued refusal.** Unsupported or over-budget inputs return
   `UNKNOWN`/`None`; they must not be interpreted as nonzero.
5. **Negative cache where useful.** Cache deterministic structural
   inapplicability, never a merely inconclusive mathematical result.
6. **Independent verification for candidates.** Heuristic relation finders
   such as PSLQ do not certify their own candidates.
7. **Tests.** Add positive, negative, edge/boundary, refusal, cache, and routing
   tests. Cross-check with an independent exact method when one exists.
8. **Performance contract.** Demonstrate that inapplicable or oversized inputs
   refuse cheaply, then compare the standard benchmark before and after.
9. **Documentation.** Update capabilities, limitations, soundness, and the
   budget table only where the new method changes those contracts.

## Coverage

CI records branch coverage with `pytest-cov` and uploads the XML report. The
report is diagnostic rather than an arbitrary global percentage gate. Branch
coverage is especially useful here because conservative refusal paths are part
of correctness. If module-specific thresholds are introduced later, critical
routing/soundness modules should receive them before broad leaf helpers.

## Release gates

`tests/test_release_gate.py` contains adversarial cases for branch safety,
poles, nonfinite values, approximate inputs, dependent radicals, near-zero
algebraic constants, and intentionally unresolved expressions. Returning
`None` is preferable to weakening these cases.

The package job builds wheel/sdist artifacts, checks metadata, installs the
wheel, verifies `py.typed`, and runs the standalone smoke test. The publishing
workflow additionally smoke-tests the built wheel on the oldest and newest
supported Python versions before PyPI publication.

## Supported environments

CI covers Python 3.9-3.14 on Linux, declared minimum SymPy/mpmath versions,
FLINT-enabled configurations, and targeted Windows/macOS smoke tests. Timeout
support degrades safely where `SIGALRM` is unavailable or execution is outside
the main thread.
