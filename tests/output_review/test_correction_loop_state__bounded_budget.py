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

from autofirm.output_review.correction_loop_state import (
    CorrectionLoopState,
    CorrectionSendBack,
)
from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.review_finding_and_severity_contracts import (
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
    ReviewFinding,
)
from autofirm.output_review.review_verdict_contract import ReviewVerdict

_FIXED_AT = datetime(2024, 1, 1, tzinfo=UTC)  # injected clock — never now()


def _finding(severity: CheckSeverity, idx: int = 0) -> ReviewFinding:
    """A valid synthetic finding of a given severity (distinct locator per idx)."""
    return ReviewFinding(
        check_id=ReviewCheckId.ACCOUNTING_IDENTITY,
        severity=severity,
        defect_class=DefectClass.PURE_LOGIC,
        message="A != L + E",
        locator=f"Sheet1!B{idx}",
        expected="A=100",
        actual="L+E=99",
    )


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


# ---- EXACT message text — kill mutmut string-literal mutants (in != ==) ---------
#
# mutmut wraps each string literal as "XX...XX", which a substring `in` check would
# still pass — so every message is pinned with `==` on the FULL string. The two
# computed f-string numbers (max_attempts+1 and max_attempts) are pinned to concrete
# values so a mutant flipping the arithmetic (+1 -> -1/+2) is killed too.


def test_attempt_below_one_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as excinfo:
        CorrectionLoopState(attempt=0, max_attempts=3)
    assert str(excinfo.value) == "CorrectionLoopState attempt must be >= 1"


def test_max_attempts_below_one_message_is_exact() -> None:
    # attempt=1 is valid, so the failure is specifically the max_attempts guard.
    with pytest.raises(OutputReviewError) as excinfo:
        CorrectionLoopState(attempt=1, max_attempts=0)
    assert str(excinfo.value) == "CorrectionLoopState max_attempts must be >= 1"


def test_attempt_out_of_range_message_is_exact_with_computed_ceiling() -> None:
    # attempt=6, max_attempts=3 -> ceiling sentinel is 4; the message must spell out
    # both the literal text AND the computed max_attempts+1=4 exactly (a +1->-1/+2
    # mutant inside the f-string changes the number and is killed by this ==).
    with pytest.raises(OutputReviewError) as excinfo:
        CorrectionLoopState(attempt=6, max_attempts=3)
    assert str(excinfo.value) == (
        "CorrectionLoopState attempt out of range: attempt=6 > max_attempts+1=4"
    )


def test_budget_exhausted_message_is_exact_with_max_attempts() -> None:
    # Exhausted state (attempt=2 > max_attempts=1); advancing must refuse with the
    # exact message carrying the concrete max_attempts=1 value.
    exhausted = CorrectionLoopState(attempt=2, max_attempts=1)
    with pytest.raises(OutputReviewError) as excinfo:
        exhausted.record_and_advance(_failing_verdict(0))
    assert str(excinfo.value) == (
        "CorrectionLoopState budget exhausted: cannot advance past max_attempts=1"
    )


# ---- default-value mutant: `history: ... = ()` -> `= None` ----------------------


def test_history_defaults_to_empty_tuple_not_none() -> None:
    # Omitting history must yield an empty TUPLE, not None — kills the `= None`
    # default mutant (which would either set None or fail construction outright).
    state = CorrectionLoopState(attempt=1, max_attempts=3)
    assert state.history == ()
    assert isinstance(state.history, tuple)


# ---- boundary: budget_exhausted on/just-under, just-over (exact == comparator) --


def test_budget_exhausted_is_false_one_below_ceiling() -> None:
    # attempt = max_attempts-1 < max_attempts: clearly not exhausted (guards a
    # `>` -> `>=` mutant from the just-under side).
    assert CorrectionLoopState(attempt=2, max_attempts=3).budget_exhausted is False


# ---- CorrectionSendBack EXACT message text (same module) — string-mutant kills --


def test_send_back_blank_ref_message_is_exact() -> None:
    # Other fields valid so the blank-ref guard is the sole failure surfaced.
    with pytest.raises(OutputReviewError) as excinfo:
        CorrectionSendBack(
            artifact_ref="  ",
            blocking_findings=(_finding(CheckSeverity.BLOCKING),),
            attempt=1,
        )
    assert str(excinfo.value) == "CorrectionSendBack artifact_ref must be non-blank"


def test_send_back_sub_one_attempt_message_is_exact() -> None:
    # Ref + findings valid; only the attempt guard should fire.
    with pytest.raises(OutputReviewError) as excinfo:
        CorrectionSendBack(
            artifact_ref="art-1",
            blocking_findings=(_finding(CheckSeverity.BLOCKING),),
            attempt=0,
        )
    assert str(excinfo.value) == "CorrectionSendBack attempt must be >= 1"


def test_send_back_empty_findings_message_is_exact_two_part() -> None:
    # The two adjacent string literals are concatenated into ONE message; pin the
    # whole joined string so a mutant on EITHER literal half is killed.
    with pytest.raises(OutputReviewError) as excinfo:
        CorrectionSendBack(artifact_ref="art-1", blocking_findings=(), attempt=1)
    assert str(excinfo.value) == (
        "CorrectionSendBack.blocking_findings must be non-empty: "
        "you never send back a passing artifact"
    )


def test_send_back_advisory_member_message_is_exact_two_part() -> None:
    # Non-empty but carries an ADVISORY finding -> the ONLY-BLOCKING guard fires;
    # pin the full concatenated two-literal message.
    with pytest.raises(OutputReviewError) as excinfo:
        CorrectionSendBack(
            artifact_ref="art-1",
            blocking_findings=(_finding(CheckSeverity.ADVISORY),),
            attempt=1,
        )
    assert str(excinfo.value) == (
        "CorrectionSendBack.blocking_findings must contain ONLY BLOCKING "
        "findings: advisory findings do not justify a send-back"
    )
