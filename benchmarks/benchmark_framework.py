"""Warm isolated measurements of the new assumption/domain dispatch cases."""

import json, statistics, time, sys
from pathlib import Path
import sympy as s
from exprtools import MathematicalContext, SimplificationBudget, refine, simplify

x = s.Symbol("x")
budget = SimplificationBudget(seconds=1)
cases = [
    ("real_even_root", lambda: refine(s.sqrt(x * x), s.Q.real(x), budget=budget)),
    ("positive_absolute", lambda: refine(s.Abs(x), x > 0, budget=budget)),
    ("real_log_exp", lambda: refine(s.log(s.exp(x)), s.Q.real(x), budget=budget)),
    ("complex_log_refusal", lambda: refine(s.log(s.exp(x)), budget=budget)),
    ("pointwise_hole_refusal", lambda: simplify((x * x - 1) / (x - 1), budget=budget)),
    (
        "guarded_rational",
        lambda: simplify((x * x - 1) / (x - 1), s.Ne(x, 1), budget=budget),
    ),
    (
        "positive_gamma",
        lambda: simplify(s.gamma(x + 2) / s.gamma(x), x > 0, budget=budget),
    ),
]
report = {}
for name, fn in cases:
    expected = fn()
    times = []
    for _ in range(100):
        start = time.perf_counter()
        result = fn()
        times.append(time.perf_counter() - start)
        assert result == expected
    report[name] = dict(
        n=100,
        total_seconds=sum(times),
        median_seconds=statistics.median(times),
        p95_seconds=sorted(times)[94],
        output=s.srepr(expected),
    )
output = Path(sys.argv[1] if len(sys.argv) > 1 else "framework-benchmarks.json")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
