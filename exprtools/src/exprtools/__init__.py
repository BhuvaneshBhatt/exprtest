"""Fast symbolic expression predicates with exact, numeric, and heuristic methods."""

from importlib.metadata import PackageNotFoundError, version

from ._domains import (
    ElementOf,
    is_algebraic,
    is_integer,
    is_prime,
    is_rational,
    is_real,
    number_kind,
)
from ._result import Verdict, ZeroClassification
from .core import profile_zerotest, zerotest

try:
    __version__ = version("exprtools")
except PackageNotFoundError:
    __version__ = "0+unknown"

__all__ = [
    "ElementOf",
    "Verdict",
    "ZeroClassification",
    "is_algebraic",
    "is_integer",
    "is_prime",
    "is_rational",
    "is_real",
    "number_kind",
    "profile_zerotest",
    "zerotest",
]

# General expression tools do not participate in the predicate proof cascade.
from .context import MathematicalContext
from .evidence import TransformationEvidence
from .recurrence import (
    RecurrenceFamilies,
    RecurrenceSimplificationResult,
    simplify_recurrences,
)
from .refinement import refine
from .simplification import (
    DEFAULT_REGISTRY,
    SimplificationBudget,
    SimplificationResult,
    Transformation,
    TransformationRegistry,
    simplify,
)

__all__ += [
    "MathematicalContext",
    "TransformationEvidence",
    "RecurrenceFamilies",
    "RecurrenceSimplificationResult",
    "simplify_recurrences",
    "refine",
    "simplify",
    "SimplificationBudget",
    "SimplificationResult",
    "Transformation",
    "TransformationRegistry",
    "DEFAULT_REGISTRY",
]

from .algebraic import StructuralSeparationBound, structural_separation_bound

__all__ += ["StructuralSeparationBound", "structural_separation_bound"]
