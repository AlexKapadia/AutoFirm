"""DoD-gate tests: DONE iff EVERY required gate passes — never on a partial.

Proves the §4.9.7 Definition-of-Done is fail-closed: the verdict is DONE only on
the AND of every required gate being present AND passing; a single failing gate,
a single missing gate, or an empty result set yields NOT_DONE with the exact
blockers named. Includes the load-bearing Hypothesis property: over arbitrary
pass/fail assignments AND arbitrary omitted gates, evaluate() returns DONE iff
the set of passing gates equals REQUIRED_GATES — and the blocking list equals
exactly the missing-or-failed set. Synthetic only; no network.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.design_product.ui_definition_of_done_gate import (
    REQUIRED_GATES,
    DoneVerdict,
    GateResult,
    QualityGate,
    UiDefinitionOfDoneGate,
    UiDoneEvaluation,
)

_ALL_GATES = sorted(QualityGate, key=lambda g: g.value)


def _all_passing() -> tuple[GateResult, ...]:
    return tuple(GateResult(gate=g, passed=True, reason="evidence: green") for g in QualityGate)


# --------------------------------------------------------------------------- #
# Canonical DONE / NOT_DONE.                                                   #
# --------------------------------------------------------------------------- #


def test_all_gates_passing_is_done_with_no_blockers() -> None:
    ev = UiDefinitionOfDoneGate(results=_all_passing()).evaluate()
    assert ev.verdict is DoneVerdict.DONE
    assert ev.blocking_gates == ()
    assert ev.blocking_reasons == ()


def test_empty_result_set_is_not_done_all_gates_block() -> None:
    # Fail-closed: no evidence at all -> every required gate blocks (never DONE).
    ev = UiDefinitionOfDoneGate(results=()).evaluate()
    assert ev.verdict is DoneVerdict.NOT_DONE
    assert set(ev.blocking_gates) == REQUIRED_GATES


@pytest.mark.parametrize("failed_gate", _ALL_GATES)
def test_single_failed_gate_blocks_done_and_is_named(failed_gate: QualityGate) -> None:
    results = tuple(
        GateResult(
            gate=g,
            passed=(g is not failed_gate),
            reason=("fail here" if g is failed_gate else "ok"),
        )
        for g in QualityGate
    )
    ev = UiDefinitionOfDoneGate(results=results).evaluate()
    assert ev.verdict is DoneVerdict.NOT_DONE
    assert ev.blocking_gates == (failed_gate,)
    assert ev.blocking_reasons == ("fail here",)


@pytest.mark.parametrize("missing_gate", _ALL_GATES)
def test_single_missing_gate_blocks_done(missing_gate: QualityGate) -> None:
    # Omitting a gate cannot ship: a missing result is treated as a blocker.
    results = tuple(
        GateResult(gate=g, passed=True, reason="ok") for g in QualityGate if g is not missing_gate
    )
    ev = UiDefinitionOfDoneGate(results=results).evaluate()
    assert ev.verdict is DoneVerdict.NOT_DONE
    assert ev.blocking_gates == (missing_gate,)
    assert "missing result" in ev.blocking_reasons[0]


# --------------------------------------------------------------------------- #
# Construction-time and self-consistency guards.                              #
# --------------------------------------------------------------------------- #


def test_duplicate_gate_result_is_refused() -> None:
    dup = (
        GateResult(gate=QualityGate.RESPONSIVE, passed=True, reason="a"),
        GateResult(gate=QualityGate.RESPONSIVE, passed=False, reason="b"),
    )
    with pytest.raises(ValidationError, match="duplicate result"):
        UiDefinitionOfDoneGate(results=dup)


def test_gate_result_blank_reason_refused() -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        GateResult(gate=QualityGate.RESPONSIVE, passed=True, reason="  ")


def test_evaluation_cannot_claim_done_with_blockers() -> None:
    # The verdict/blocker self-consistency guard: DONE iff zero blockers.
    with pytest.raises(ValidationError, match="DONE iff there are zero blocking gates"):
        UiDoneEvaluation(
            verdict=DoneVerdict.DONE,
            blocking_gates=(QualityGate.WCAG_2_2_AA,),
            blocking_reasons=("x",),
        )


def test_evaluation_cannot_claim_not_done_with_zero_blockers() -> None:
    with pytest.raises(ValidationError, match="DONE iff there are zero blocking gates"):
        UiDoneEvaluation(verdict=DoneVerdict.NOT_DONE, blocking_gates=(), blocking_reasons=())


def test_evaluation_mismatched_gate_and_reason_counts_refused() -> None:
    with pytest.raises(ValidationError, match="exactly one reason"):
        UiDoneEvaluation(
            verdict=DoneVerdict.NOT_DONE,
            blocking_gates=(QualityGate.WCAG_2_2_AA, QualityGate.RESPONSIVE),
            blocking_reasons=("only one",),
        )


# --------------------------------------------------------------------------- #
# The load-bearing property: DONE iff passing-set == REQUIRED_GATES.           #
# --------------------------------------------------------------------------- #


@st.composite
def _arbitrary_result_sets(draw: st.DrawFn) -> tuple[GateResult, ...]:
    # Independently choose, for each gate, whether it is present and pass/fail —
    # so the strategy spans omissions AND failures, not just one or the other.
    results: list[GateResult] = []
    for gate in QualityGate:
        present = draw(st.booleans())
        if present:
            passed = draw(st.booleans())
            results.append(GateResult(gate=gate, passed=passed, reason="ok" if passed else "no"))
    return tuple(results)


@given(results=_arbitrary_result_sets())
def test_property_done_iff_every_required_gate_present_and_passed(
    results: tuple[GateResult, ...],
) -> None:
    passing = {r.gate for r in results if r.passed}
    failed_or_missing = REQUIRED_GATES - passing
    ev = UiDefinitionOfDoneGate(results=results).evaluate()
    expected_done = passing == REQUIRED_GATES
    assert (ev.verdict is DoneVerdict.DONE) == expected_done
    # The blocking set is exactly the missing-or-failed gates — why matches what.
    assert set(ev.blocking_gates) == failed_or_missing
    assert len(ev.blocking_gates) == len(ev.blocking_reasons)


@given(results=_arbitrary_result_sets())
def test_property_done_never_returned_on_any_proper_subset(
    results: tuple[GateResult, ...],
) -> None:
    # Hard restatement: if even one required gate is not passing, NEVER DONE.
    passing = {r.gate for r in results if r.passed}
    ev = UiDefinitionOfDoneGate(results=results).evaluate()
    if passing < REQUIRED_GATES:  # proper subset (or any non-superset)
        assert ev.verdict is DoneVerdict.NOT_DONE
