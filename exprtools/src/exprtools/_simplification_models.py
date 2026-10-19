"""Resource limits and result types shared by refinement and simplification."""

import math
import time
from dataclasses import dataclass

import sympy as sp

from .evidence import TransformationEvidence


@dataclass(frozen=True)
class SimplificationBudget:
    max_steps: int = 24
    max_ops: int = 240
    seconds: float = 0.25

    def __post_init__(self):
        if any(
            isinstance(n, bool) or not isinstance(n, int) or n < 0
            for n in (self.max_steps, self.max_ops)
        ):
            raise ValueError("step and operation limits must be nonnegative integers")
        if (
            not isinstance(self.seconds, (int, float))
            or not math.isfinite(self.seconds)
            or self.seconds < 0
        ):
            raise ValueError("seconds must be finite and nonnegative")


@dataclass(frozen=True)
class SimplificationResult:
    original: sp.Basic
    expression: sp.Basic
    evidence: tuple[TransformationEvidence, ...] = ()
    steps: int = 0
    stopped: str | None = None
    domain: str = "pointwise"

    @property
    def domain_preserved(self):
        return self.domain == "pointwise" or self.original == self.expression


class _Run:
    def __init__(self, budget):
        self.budget = budget
        self.deadline = time.monotonic() + budget.seconds
        self.steps = 0
        self.evidence = []
        self.stopped = None

    def available(self):
        if self.steps >= self.budget.max_steps:
            self.stopped = "step budget"
        elif time.monotonic() >= self.deadline:
            self.stopped = "time budget"
        return self.stopped is None

    def remaining(self):
        return SimplificationBudget(
            max(0, self.budget.max_steps - self.steps),
            self.budget.max_ops,
            max(0, self.deadline - time.monotonic()),
        )
