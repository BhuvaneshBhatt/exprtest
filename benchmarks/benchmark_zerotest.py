"""Microbenchmark for the bounded public zero oracle."""

from __future__ import annotations

import statistics
import time

import sympy as sp

from exprtest import zerotest
from exprtest._cache import cache_clear


def cases(count: int = 5000):
    roots = [sp.sqrt(2), sp.sqrt(3), sp.sqrt(5), sp.sqrt(7)]
    data = []
    for i in range(count):
        k = i % 15
        n = sp.Integer(i % 97 + 1)
        if k == 0:
            data.append(n)
        elif k == 1:
            data.append(sp.Mul(n, sp.pi, evaluate=False))
        elif k == 2:
            data.append(sp.exp(roots[i % len(roots)], evaluate=False))
        elif k == 3:
            data.append(sp.log(n + 1, evaluate=False))
        elif k == 4:
            r = roots[i % len(roots)]
            data.append(sp.Add(r, -r, evaluate=False))
        elif k == 5:
            angle = sp.pi * sp.Rational((i % 5) + 1, 7)
            data.append(sp.Add(sp.sin(angle), -sp.sin(angle), evaluate=False))
        elif k == 6:
            data.append(
                sp.Add(
                    sp.log(2, evaluate=False),
                    -sp.log(2, evaluate=False),
                    evaluate=False,
                )
            )
        elif k == 7:
            data.append(sp.sqrt(n + 1))
        elif k == 8:
            data.append(sp.sin(sp.Rational((i % 11) + 1, 13)))
        elif k == 9:
            data.append(sp.Add(sp.pi**3, 2 * sp.pi, 1, evaluate=False))
        elif k == 10:
            data.append((sp.pi**2 + 1) / (sp.pi + 2))
        elif k == 11:
            data.append(
                sp.Add(
                    sp.log(12, evaluate=False),
                    -2 * sp.log(2, evaluate=False),
                    -sp.log(3, evaluate=False),
                    evaluate=False,
                )
            )
        elif k == 12:
            g = sp.gamma(sp.Rational(5, 2), evaluate=False)
            data.append(sp.Add(g, -3 * sp.sqrt(sp.pi) / 4, evaluate=False))
        elif k == 13:
            data.append(
                sp.Add(
                    sp.cos(2 * sp.pi / 7),
                    sp.cos(4 * sp.pi / 7),
                    sp.cos(6 * sp.pi / 7),
                    sp.Rational(1, 2),
                    evaluate=False,
                )
            )
        elif k == 14:
            data.append(
                sp.Add(sp.zeta(4, evaluate=False), -(sp.pi**4) / 90, evaluate=False)
            )
    return data


def run(data, *, cache: bool):
    times = []
    verdicts = {True: 0, False: 0, None: 0}
    start = time.perf_counter()
    for term in data:
        one = time.perf_counter()
        ans = zerotest(term, use_cache=cache)
        times.append(time.perf_counter() - one)
        verdicts[ans] += 1
    elapsed = time.perf_counter() - start
    return elapsed, times, verdicts


def main():
    data = cases()
    cache_clear()
    cold, cold_times, cold_v = run(data, cache=False)

    repeated = data[:125] * 40
    cache_clear()
    warm, warm_times, warm_v = run(repeated, cache=True)

    def line(name, elapsed, times, verdicts):
        ordered = sorted(times)
        p95 = ordered[int(0.95 * (len(ordered) - 1))]
        print(
            f"{name}: n={len(times)} total={elapsed:.4f}s "
            f"rate={len(times) / elapsed:.1f}/s median={statistics.median(times) * 1e6:.1f}us "
            f"p95={p95 * 1e6:.1f}us verdicts={verdicts}"
        )

    line("cold", cold, cold_times, cold_v)
    line("repeated", warm, warm_times, warm_v)


if __name__ == "__main__":
    main()
