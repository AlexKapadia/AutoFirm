"""Teeth-tests for CorrectionLoopState — the anti-INFINITE-LOOP budget proof.

These prove the correction loop is BOUNDED by construction: a loop started with a
budget of ``N`` advances exactly ``N`` times and then refuses to advance, so the
gate can never spin forever (CLAUDE.md §3.6 anti-overfit + §5.6 fail-closed). They
also prove ``record_and_advance`` is functional/frozen (the receiver is never
mutated) and that history accumulates in order. Each test would FAIL if the bound,
the exhaustion guard, or the frozen-functional contract were wrong — none is
tautological. Boundary budgets ``N=1`` and ``N=3`` plus a hypothesis property over
random budgets ``1..10`` pin the bound exactly.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.output_review.correction_loop_state import CorrectionLoopState
from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.review_finding_and_severity_contracts import (
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
    ReviewFinding,
)
from autofirm.output_review.review_verdict_contract import ReviewVerdict

_FIXED_AT = datetime(2024, 1, 1, tzinfo=UTC)  # injected clock — never now()


def _failing_verdict(idx: int = 0) -> ReviewVerdict:
    """A verdict that FAILS (carries one BLOCKING finding), distinct per idx."""
    finding = ReviewFinding(
        check_id=ReviewCheckId.ACCOUNTING_IDENTITY,
        severity=CheckSeverity.BLOCKING,
        defect_class=DefectClass.PURE_LOGIC,
        message="A != L + E",
        locator=f"Sheet1!B{idx}",
        expected="A=100",
        actual=f"L+E={99 - idx}",
    )
    return ReviewVerdict(
        artifact_ref=f"art-{idx}", findings=(finding,), reviewed_at=_FIXED_AT
    )


# ---- construction / validation boundaries --------------------------------------


def test_start_opens_at_attempt_one_empty_history() -> None:
    state = CorrectionLoopState.start(max_attempts=3)
    assert state.attempt == 1
    assert state.max_attempts == 3
    assert state.history == ()
    assert state.budget_exhausted is False


@pytest.mark.parametrize("bad", [0, -1])
def test_start_with_sub_one_budget_refused(bad: int) -> None:
    # fail-closed: a budget that could never review anything is rejected.
    with pytest.raises(OutputReviewError):
        CorrectionLoopState.start(max_attempts=bad)


@pytest.mark.parametrize("bad", [0, -5])
def test_attempt_below_one_refused(bad: int) -> None:
    with pytest.raises(OutputReviewError):
        CorrectionLoopState(attempt=bad, max_attempts=3)


def test_attempt_above_ceiling_plus_one_refused() -> None:
    # max_attempts+1 is the legal post-exhaustion sentinel; one beyond is corrupt.
    with pytest.raises(OutputReviewError):
        CorrectionLoopState(attempt=5, max_attempts=3)


def test_attempt_exactly_ceiling_plus_one_is_legal_and_exhausted() -> None:
    # The boundary: attempt == max_attempts+1 is the exhausted sentinel, accepted.
    state = CorrectionLoopState(attempt=4, max_attempts=3)
    assert state.budget_exhausted is True


# ---- budget_exhausted is exact at the boundary ---------------------------------


def test_exhausted_false_at_ceiling_true_one_past() -> None:
    # attempt == max_attempts: one attempt still remains -> NOT exhausted.
    assert CorrectionLoopState(attempt=3, max_attempts=3).budget_exhausted is False
    # attempt == max_attempts+1: no attempt remains -> exhausted.
    assert CorrectionLoopState(attempt=4, max_attempts=3).budget_exhausted is True


# ---- THE anti-infinite-loop proof: bounded to exactly N advances ---------------


@pytest.mark.parametrize("budget", [1, 3])
def test_advances_exactly_budget_times_then_refuses(budget: int) -> None:
    """start(N) advances N times, is exhausted after the Nth, then refuses (N=1,3)."""
    state = CorrectionLoopState.start(max_attempts=budget)
    for i in range(budget):
        assert state.budget_exhausted is False  # an attempt remains each iteration
        state = state.record_and_advance(_failing_verdict(i))
    # After exactly N advances the budget is spent and history holds all N verdicts.
    assert state.budget_exhausted is True
    assert len(state.history) == budget
    assert state.attempt == budget + 1
    # A further advance is refused fail-closed — the loop CANNOT continue forever.
    with pytest.raises(OutputReviewError):
        state.record_and_advance(_failing_verdict(99))


def test_record_and_advance_on_already_exhausted_refused() -> None:
    exhausted = CorrectionLoopState(attempt=2, max_attempts=1)
    assert exhausted.budget_exhausted is True
    with pytest.raises(OutputReviewError):
        exhausted.record_and_advance(_failing_verdict(0))


# ---- functional / frozen: original never mutated, history ordered --------------


def test_record_and_advance_is_functional_original_unchanged() -> None:
    original = CorrectionLoopState.start(max_attempts=3)
    advanced = original.record_and_advance(_failing_verdict(1))
    # The returned state is NEW; the receiver is untouched (frozen-functional).
    assert advanced is not original
    assert original.attempt == 1
    assert original.history == ()
    assert advanced.attempt == 2
    assert len(advanced.history) == 1


def test_history_accumulates_in_order() -> None:
    state = CorrectionLoopState.start(max_attempts=3)
    v0, v1, v2 = _failing_verdict(0), _failing_verdict(1), _failing_verdict(2)
    state = state.record_and_advance(v0)
    state = state.record_and_advance(v1)
    state = state.record_and_advance(v2)
    # Order is preserved exactly — the loop's audit trail is the verdict sequence.
    assert state.history == (v0, v1, v2)


def test_frozen_state_rejects_mutation() -> None:
    state = CorrectionLoopState.start(max_attempts=2)
    with pytest.raises(ValidationError):  # pydantic frozen model rejects mutation
        state.attempt = 2  # type: ignore[misc]


# ---- PROPERTY: bounded to EXACTLY max_attempts advances, never more -------------


@settings(max_examples=300)
@given(budget=st.integers(min_value=1, max_value=10))
def test_property_advances_exactly_budget_then_exhausted(budget: int) -> None:
    """For ANY budget 1..10: exactly `budget` advances reach exhaustion, no more."""
    state = CorrectionLoopState.start(max_attempts=budget)
    for i in range(budget):
        # Never exhausted before the budget is spent — the loop always makes progress.
        assert state.budget_exhausted is False
        state = state.record_and_advance(_failing_verdict(i))
    # Exactly at the bound: exhausted, history == budget, attempt == budget+1.
    assert state.budget_exhausted is True
    assert len(state.history) == budget
    assert state.attempt == budget + 1
    # Beyond the bound is structurally impossible — never negative, never unbounded.
    with pytest.raises(OutputReviewError):
        state.record_and_advance(_failing_verdict(budget))
