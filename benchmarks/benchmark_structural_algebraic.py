"""Compare stage-4 and stage-5 algorithms using the same process and inputs."""

import argparse
import importlib.util
import json
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import sympy as s
from exprtools._cache import cache_clear
from exprtools._structural_gap import (
    structural_algebraic_test,
    structural_separation_bound,
)

from exprtools import zerotest


def baseline(name, path):
    spec = importlib.util.spec_from_file_location("exprtools." + name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--baseline-ref", default="ccc7b78744cc76551da742de80f8b55d8e01b31b"
)
parser.add_argument("--output", type=Path, default=Path("algorithm-benchmarks.json"))
args = parser.parse_args()
repository = Path(__file__).resolve().parents[1]
temporary = tempfile.TemporaryDirectory()


def baseline_source(filename):
    source = subprocess.check_output(
        ["git", "show", f"{args.baseline_ref}:exprtools/src/exprtools/{filename}"],
        cwd=repository,
    )
    target = Path(temporary.name) / filename
    target.write_bytes(source)
    return target


old = baseline("_stage4_algebraic", baseline_source("_algebraic.py"))
core = baseline("_stage4_core", baseline_source("core.py"))
core.exact_algebraic_number_test = old.exact_algebraic_number_test


def verdict(result):
    return result.verdict.name if hasattr(result, "verdict") else str(result)


def measure(fn, e, n, cold=False):
    times = []
    values = []
    for _ in range(n):
        if cold:
            cache_clear()
        start = time.perf_counter()
        v = fn(e)
        times.append(time.perf_counter() - start)
        values.append(verdict(v))
    assert len(set(values)) == 1, values
    return dict(
        n=n,
        median_seconds=statistics.median(times),
        p95_seconds=sorted(times)[int(0.95 * (n - 1))],
        total_seconds=sum(times),
        verdict=values[0],
    )


cases = {
    "quadratic_nested_zero": s.Add(
        s.Pow(3 + 2 * s.sqrt(2), s.S.Half, evaluate=False),
        -1,
        -s.sqrt(2),
        evaluate=False,
    ),
    "dependent_radicals_zero": s.Add(
        s.sqrt(2),
        s.sqrt(3),
        -s.Pow(5 + 2 * s.sqrt(6), s.S.Half, evaluate=False),
        evaluate=False,
    ),
    "rational_nested_zero": s.Add(
        s.sqrt(s.Rational(2, 3)),
        s.sqrt(s.Rational(5, 7)),
        -s.Pow(
            s.Rational(29, 21) + 2 * s.sqrt(s.Rational(10, 21)),
            s.S.Half,
            evaluate=False,
        ),
        evaluate=False,
    ),
    "nearby_nonzero": s.Add(
        s.Pow(10**40 + 1, s.S.Half, evaluate=False), -(10**20), evaluate=False
    ),
}
report = {}
for name, e in cases.items():
    print(name, flush=True)
    row = {"expression": s.srepr(e), "bound": str(structural_separation_bound(e))}
    for mode, cold, count in [("cold", True, 7), ("warm", False, 60)]:
        cache_clear()
        old.exact_algebraic_number_test(e)
        structural_algebraic_test(e)
        b = measure(old.exact_algebraic_number_test, e, count, cold)
        a = measure(structural_algebraic_test, e, count, cold)
        assert b["verdict"] == a["verdict"], (name, b, a)
        row[mode] = dict(
            baseline=b, candidate=a, speedup=b["median_seconds"] / a["median_seconds"]
        )
    old_public = measure(
        lambda x: core.zerotest(x, use_cache=False, confidence="certified"), e, 20
    )
    new_public = measure(
        lambda x: zerotest(x, use_cache=False, confidence="certified"), e, 20
    )
    assert old_public["verdict"] == new_public["verdict"]
    row["public"] = dict(
        baseline=old_public,
        candidate=new_public,
        speedup=old_public["median_seconds"] / new_public["median_seconds"],
    )
    report[name] = row
report = dict(
    environment=dict(
        python=platform.python_version(),
        sympy=s.__version__,
        baseline_ref=args.baseline_ref,
    ),
    cases=report,
)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + "\n")
temporary.cleanup()
print(json.dumps(report, indent=2))
