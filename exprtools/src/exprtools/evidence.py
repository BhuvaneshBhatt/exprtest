"""Package-independent transformation provenance."""

from dataclasses import dataclass

import sympy as sp


@dataclass(frozen=True)
class TransformationEvidence:
    method: str
    statement: str
    substitutions: tuple[tuple[sp.Basic, sp.Basic], ...] = ()
    value: sp.Expr | None = None
