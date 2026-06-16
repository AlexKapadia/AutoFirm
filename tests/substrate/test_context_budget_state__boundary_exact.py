"""Adversarial + property tests for the context-budget exhaustion boundary.

The handoff decision is boundary-exact: a session must hand off at the EXACT
threshold token, not one token early or late. These tests pin the on/just-under/
just-over edges, prove over-consumption clamps (never wraps un-exhausted), and
property-check that consumption is monotone and stays within [0, limit].
Synthetic only.
"""

from __future__ import annotations

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.substrate.context_budget_state import ContextBudgetState


@pytest.mark.unit
@pytest.mark.parametrize(
    ("limit", "threshold", "consumed", "expected"),
    [
        (1000, 0.8, 799, False),  # just under the 800-token threshold
        (1000, 0.8, 800, True),  # EXACTLY at the threshold -> must hand off
        (1000, 0.8, 801, True),  # just over
        (1000, 1.0, 999, False),  # threshold==limit: only the last token trips it
        (1000, 1.0, 1000, True),  # full window at threshold 1.0
        (3, 0.5, 1, False),  # ceil(0.5*3)=2 -> 1 is under
        (3, 0.5, 2, True),  # ceil(0.5*3)=2 -> 2 is exactly at
    ],
)
def test_is_exhausted_is_boundary_exact(
    limit: int, threshold: float, consumed: int, expected: bool
) -> None:
    budget = ContextBudgetState(
        limit_tokens=limit, consumed_tokens=consumed, handoff_threshold=threshold
    )
    assert budget.is_exhausted() is expected


@pytest.mark.unit
def test_consume_clamps_at_limit_never_wraps() -> None:
    budget = ContextBudgetState(limit_tokens=100, consumed_tokens=90, handoff_threshold=0.5)
    # Over-consume by a mile: must clamp to the limit, staying exhausted.
    clamped = budget.consume(10_000)
    assert clamped.consumed_tokens == 100
    assert clamped.remaining_tokens() == 0
    assert clamped.is_exhausted() is True


@pytest.mark.unit
def test_consume_negative_is_refused() -> None:
    budget = ContextBudgetState(limit_tokens=100, consumed_tokens=0, handoff_threshold=0.5)
    with pytest.raises(ValueError, match="negative"):  # fail-closed
        budget.consume(-1)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("limit", "consumed", "threshold"),
    [
        (0, 0, 0.5),  # zero window refused
        (-1, 0, 0.5),  # negative window refused
        (100, -1, 0.5),  # negative consumed refused
        (100, 101, 0.5),  # consumed > limit refused
        (100, 0, 0.0),  # threshold 0 refused (would hand off instantly)
        (100, 0, 1.1),  # threshold > 1 refused (could never fire)
    ],
)
def test_invalid_budget_construction_is_refused(
    limit: int, consumed: int, threshold: float
) -> None:
    with pytest.raises(ValidationError):  # fail-closed at construction
        ContextBudgetState(
            limit_tokens=limit, consumed_tokens=consumed, handoff_threshold=threshold
        )


@pytest.mark.property
@given(
    limit=st.integers(min_value=1, max_value=1_000_000),
    threshold=st.floats(min_value=0.01, max_value=1.0),
    consumed=st.integers(min_value=0),
)
def test_property_exhaustion_matches_ceil_threshold(
    limit: int, threshold: float, consumed: int
) -> None:
    """is_exhausted iff consumed >= ceil(threshold*limit), over arbitrary budgets."""
    consumed = min(consumed, limit)  # keep within the validated invariant
    budget = ContextBudgetState(
        limit_tokens=limit, consumed_tokens=consumed, handoff_threshold=threshold
    )
    expected_threshold = math.ceil(threshold * limit)
    assert budget.is_exhausted() == (consumed >= expected_threshold)


@pytest.mark.property
@given(
    limit=st.integers(min_value=1, max_value=10_000),
    adds=st.lists(st.integers(min_value=0, max_value=10_000), max_size=20),
)
def test_property_consumption_monotone_and_bounded(limit: int, adds: list[int]) -> None:
    """Any sequence of consumes keeps consumed in [0, limit] and non-decreasing."""
    budget = ContextBudgetState(limit_tokens=limit, consumed_tokens=0, handoff_threshold=1.0)
    previous = 0
    for tokens in adds:
        budget = budget.consume(tokens)
        assert 0 <= budget.consumed_tokens <= limit  # invariant holds always
        assert budget.consumed_tokens >= previous  # monotone non-decreasing
        previous = budget.consumed_tokens
