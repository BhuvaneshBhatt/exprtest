"""Public oracle and classification-contract tests."""

import pytest
import sympy as sp

from exprtest import Verdict, profile_zerotest, zerotest
from exprtest._result import ZeroClassification

x = sp.symbols("x")


@pytest.mark.parametrize(
    "expr,assumptions,expected,verdict,certainty,method",
    [
        (sp.Integer(0), True, True, Verdict.ZERO_PROVEN, "certified", "literal"),
        (sp.Integer(7), True, False, Verdict.NONZERO_PROVEN, "certified", "literal"),
        (
            sp.sin(x) + 2,
            True,
            False,
            Verdict.NONZERO_LIKELY,
            "probable",
            "numeric-probe",
        ),
        (1 / x, sp.Eq(x, 0), None, Verdict.UNKNOWN, "unknown", "definedness"),
    ],
)
def test_public_oracle_contract(
    expr, assumptions, expected, verdict, certainty, method
):
    profile = profile_zerotest(expr, assumptions=assumptions, seed=1)
    assert zerotest(expr, assumptions=assumptions, seed=1, use_cache=False) is expected
    assert profile.result is expected
    assert profile.classification.verdict is verdict
    assert profile.certainty == certainty
    assert profile.method == method


def test_probable_policy_changes_only_likely_nonzero_boolean():
    expr = sp.sin(x) + 2
    assert zerotest(expr, seed=1, use_cache=False) is False
    assert zerotest(expr, seed=1, use_cache=False, confidence="probable") is False
    assert zerotest(expr, seed=1, use_cache=False, confidence="certified") is None


def test_internal_heuristic_zero_remains_non_boolean_evidence():
    classification = ZeroClassification(Verdict.ZERO_UNPROVEN, "test-evidence")
    assert classification.is_zero is None
    assert classification.suggests_zero is True
    assert classification.proven is False
    assert classification.certainty == "heuristic"


def test_proven_and_likely_nonzero_classification_semantics_are_distinct():
    proven = ZeroClassification(Verdict.NONZERO_PROVEN, "exact")
    likely = ZeroClassification(Verdict.NONZERO_LIKELY, "witness")
    assert proven.is_zero is False
    assert likely.is_zero is False
    assert proven.certainty == "certified"
    assert likely.certainty == "probable"
