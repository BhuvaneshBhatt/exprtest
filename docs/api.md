# Public API

`exprtest` keeps its package-root API intentionally small. Lower-level exact,
cyclotomic, numeric, and routing helpers are implementation details and may
change without compatibility guarantees.

## Zero testing

### `zerotest(expr, assumptions=True, use_cache=True, *, rng=None, seed=None, confidence="probable")`

Return `True` for a proved zero, `False` for a proved nonzero value, and `None`
when the bounded oracle is inconclusive. With `confidence="probable"`, strong
one-sided `NONZERO_LIKELY` evidence may also return `False`. Probabilistic
zero-like evidence is never promoted to `True`.

### `profile_zerotest(expr, assumptions=True, *, rng=None, seed=None, confidence="probable")`

Run the same bounded oracle without the final-result cache and record stage
timings. The returned profile contains:

- `result`: the same `True` / `False` / `None` result as `zerotest()`;
- `classification`: the `ZeroClassification` produced by the oracle, including
  its `Verdict`, proof method, detail, and evidence;
- `stages`: per-stage timing and routing records;
- `total_seconds`: total profiled runtime.

Profiling is opt-in so ordinary `zerotest()` calls do not allocate timing
records.

## Number predicates

The package root exports these tri-state predicates:

- `is_prime`
- `is_integer`
- `is_rational`
- `is_real`
- `is_algebraic`

`number_kind()` provides a theorem-driven algebraic / transcendental / unknown
classification. `ElementOf()` performs lightweight membership reasoning for
supported numeric domains.

## Result types

`Verdict` distinguishes proved, heuristic, and unknown internal outcomes.
`ZeroClassification` stores the proof method and supporting metadata used by
`profile_zerotest()`.


## Understanding a `zerotest` decision

`profile_zerotest()` returns the same tri-state result as `zerotest()` and also
exposes the final method and evidence strength:

```python
profile = profile_zerotest(expr)
profile.result       # True, False, or None
profile.method       # e.g. "exact-literal", "algebraic", "numerical"
profile.certainty    # "certified", "probable", "heuristic", or "unknown"
profile.detail       # stage-specific explanation
profile.evidence     # optional compact evidence label
profile.reason       # concise combined explanation
```

With `confidence="certified"`, a Boolean result corresponds to a certified
conclusion. The default `confidence="probable"` may
promote `NONZERO_LIKELY` to `False`. Profiling always reports the underlying
classification rather than changing its certainty.

## Version and typing metadata

`exprtest.__version__` is read from installed package metadata, avoiding a
second hard-coded version source. The distribution includes `py.typed`, so
static type checkers may consume the package's inline annotations.
