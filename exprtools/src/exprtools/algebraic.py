"""Structural algebraic separation utilities.

Bounds are conditional: a positive bound alone never proves nonzeroness.
"""

from ._structural_gap import StructuralSeparationBound, structural_separation_bound

__all__ = ["StructuralSeparationBound", "structural_separation_bound"]
