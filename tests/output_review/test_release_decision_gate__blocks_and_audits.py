"""Teeth-tests for the RELEASE AUTHORITY (the lane's final delivery chokepoint).

These prove three things that would each FAIL if the gate were wrong (none is
tautological):

1. ``authorised == final_verdict.passed`` for EVERY constructible
   :class:`ReleaseDecision` — a passing verdict authorises and a failing one is
   blocked, and neither can be inverted by supplying ``authorised`` directly (the
   false-pass guard, CLAUDE.md §3.6; SYNTHESIS finding #6).
2. EVERY decision is audited — authorise -> ``SUCCESS``, deny -> ``DENY`` — with
   the exact ``artifact_ref`` / ``reason`` / ``decided_at`` the decision carries.
3. The gate FAILS CLOSED: if the audit write raises, ``decide`` raises and returns
   no decision — an unaudited release is forbidden (CLAUDE.md §5.6).

All inputs are synthetic; no network; the clock is injected (never ``now()``).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.audit.audit_record_contract import AuditOutcome
from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.release_decision_gate import (
    ReleaseAuditSink,
    ReleaseDecision,
    ReleaseDecisionGate,
)
from autofirm.output_review.review_finding_and_severity_contracts import (
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
    ReviewFinding,
)
from autofirm.output_review.review_verdict_contract import ReviewVerdict

_FIXED_AT = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)  # injected clock — never now()
_OTHER_AT = datetime(2030, 6, 19, 9, 30, tzinfo=UTC)  # a second distinct instant


# --------------------------------------------------------------------------------
# Synthetic verdict builders (no network, no real artifacts).
# --------------------------------------------------------------------------------
def _blocking_finding(idx: int = 0) -> ReviewFinding:
    return ReviewFinding(
        check_id=ReviewCheckId.ACCOUNTING_IDENTITY,
        severity=CheckSeverity.BLOCKING,
        defect_class=DefectClass.PURE_LOGIC,
        message="A != L + E",
        locator=f"Sheet1!B{idx}",
        expected="A=100",
        actual="L+E=99",
    )


def _advisory_finding(idx: int = 0) -> ReviewFinding:
    return ReviewFinding(
        check_id=ReviewCheckId.MODEL_ADVISORY,
        severity=CheckSeverity.ADVISORY,
        defect_class=DefectClass.EUREKA,
        message="tone could be tighter",
        locator=f"slide#{idx}",
    )


def _passing_verdict(ref: str = "art-1") -> ReviewVerdict:
    """A verdict with no blocking finding -> passed True (release authorised)."""
    return ReviewVerdict(
        artifact_ref=ref,
        findings=(_advisory_finding(1),),
        reviewed_at=_FIXED_AT,
    )


def _failing_verdict(ref: str = "art-1") -> ReviewVerdict:
    """A verdict carrying a BLOCKING finding -> passed False (release blocked)."""
    return ReviewVerdict(
        artifact_ref=ref,
        findings=(_advisory_finding(1), _blocking_finding(2)),
        reviewed_at=_FIXED_AT,
    )


# --------------------------------------------------------------------------------
# Test doubles for the injected audit seam.
# --------------------------------------------------------------------------------
class _SpySink:
    """Records every ``record`` call so a test can assert exactly what was audited."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def record(
        self,
        *,
        artifact_ref: str,
        outcome: AuditOutcome,
        reason: str,
        decided_at: datetime,
    ) -> None:
        self.calls.append(
            {
                "artifact_ref": artifact_ref,
                "outcome": outcome,
                "reason": reason,
                "decided_at": decided_at,
            }
        )


class _RaisingSink:
    """An audit seam whose write fails — exercises the fail-closed un-auditable path."""

    def __init__(self) -> None:
        self.calls = 0

    def record(
        self,
        *,
        artifact_ref: str,
        outcome: AuditOutcome,
        reason: str,
        decided_at: datetime,
    ) -> None:
        self.calls += 1
        raise RuntimeError("audit log unreachable")


def _gate(sink: ReleaseAuditSink, at: datetime = _FIXED_AT) -> ReleaseDecisionGate:
    """Build a gate with a FIXED injected clock (determinism)."""
    return ReleaseDecisionGate(sink=sink, clock=lambda: at)


# ================================================================================
# 1. PASSING verdict -> authorised release + exactly one SUCCESS audit entry.
# ================================================================================
def test_passing_verdict_authorises_and_audits_success() -> None:
    sink = _SpySink()
    decision = _gate(sink).decide(_passing_verdict("art-7"), reason="all checks green")

    assert decision.authorised is True
    assert decision.artifact_ref == "art-7"
    assert decision.decided_at == _FIXED_AT
    # exactly one audit entry, with the precise fields the decision carried.
    assert len(sink.calls) == 1
    assert sink.calls[0] == {
        "artifact_ref": "art-7",
        "outcome": AuditOutcome.SUCCESS,
        "reason": "all checks green",
        "decided_at": _FIXED_AT,
    }


# ================================================================================
# 2. FAILING verdict -> blocked (authorised False) + exactly one DENY audit entry.
# ================================================================================
def test_failing_verdict_blocks_delivery_and_audits_deny() -> None:
    sink = _SpySink()
    decision = _gate(sink).decide(_failing_verdict("art-9"), reason="blocking defect found")

    assert decision.authorised is False  # delivery BLOCKED
    assert len(sink.calls) == 1
    # a denial is LOGGED, not dropped (§5.6): outcome is DENY, not SUCCESS.
    assert sink.calls[0]["outcome"] is AuditOutcome.DENY
    assert sink.calls[0]["artifact_ref"] == "art-9"


def test_deny_outcome_is_not_success() -> None:
    # Boundary: a failing verdict must NEVER record SUCCESS (the manufactured-release attack).
    sink = _SpySink()
    _gate(sink).decide(_failing_verdict(), reason="x")
    assert sink.calls[0]["outcome"] != AuditOutcome.SUCCESS


# ================================================================================
# 3. FALSE-PASS GUARD — cannot manufacture/invert a ReleaseDecision directly.
# ================================================================================
def test_cannot_authorise_a_failing_verdict() -> None:
    # THE attack: stamp authorised=True onto a verdict that did not pass.
    with pytest.raises(OutputReviewError):
        ReleaseDecision(
            artifact_ref="art-1",
            final_verdict=_failing_verdict(),
            reason="forced",
            decided_at=_FIXED_AT,
            authorised=True,
        )


def test_cannot_deny_a_passing_verdict() -> None:
    # The symmetric dual: cannot stamp authorised=False onto a verdict that passed.
    with pytest.raises(OutputReviewError):
        ReleaseDecision(
            artifact_ref="art-1",
            final_verdict=_passing_verdict(),
            reason="forced",
            decided_at=_FIXED_AT,
            authorised=False,
        )


def test_supplied_authorised_matching_derivation_is_accepted() -> None:
    # A correctly-supplied flag round-trips (the deserialisation re-validation path).
    d = ReleaseDecision(
        artifact_ref="art-1",
        final_verdict=_failing_verdict(),
        reason="agrees",
        decided_at=_FIXED_AT,
        authorised=False,
    )
    assert d.authorised is False


def test_authorised_omitted_is_derived_from_verdict() -> None:
    d = ReleaseDecision(
        artifact_ref="art-1",
        final_verdict=_passing_verdict(),
        reason="derived",
        decided_at=_FIXED_AT,
    )
    assert d.authorised is True  # filled in from final_verdict.passed


# ================================================================================
# 4. Blank / malformed inputs are refused (fail-closed).
# ================================================================================
@pytest.mark.parametrize("bad", ["", "   ", "\t\n"])
def test_blank_reason_is_refused(bad: str) -> None:
    with pytest.raises(OutputReviewError):
        ReleaseDecision(
            artifact_ref="art-1",
            final_verdict=_passing_verdict(),
            reason=bad,
            decided_at=_FIXED_AT,
        )


@pytest.mark.parametrize("bad", ["", "   "])
def test_blank_artifact_ref_is_refused(bad: str) -> None:
    with pytest.raises(OutputReviewError):
        ReleaseDecision(
            artifact_ref=bad,
            final_verdict=_passing_verdict(),
            reason="ok",
            decided_at=_FIXED_AT,
        )


def test_extra_field_is_forbidden() -> None:
    # extra="forbid": no smuggled field can ride along on the frozen record.
    with pytest.raises(ValidationError):
        ReleaseDecision(
            artifact_ref="art-1",
            final_verdict=_passing_verdict(),
            reason="ok",
            decided_at=_FIXED_AT,
            smuggled="x",  # type: ignore[call-arg]
        )


def test_release_decision_is_frozen_cannot_flip_authorised() -> None:
    # If the record were not frozen, a caller could flip ``authorised`` to True
    # AFTER the guard ran — authorising a release the verdict never permitted.
    d = ReleaseDecision(
        artifact_ref="art-1",
        final_verdict=_failing_verdict(),
        reason="blocked",
        decided_at=_FIXED_AT,
    )
    assert d.authorised is False
    with pytest.raises(ValidationError):
        d.authorised = True  # frozen=True forbids post-construction mutation


# ================================================================================
# 5. AUDIT-FAIL FAIL-CLOSED — no authorised release escapes unaudited.
# ================================================================================
def test_audit_failure_blocks_release_and_returns_nothing() -> None:
    sink = _RaisingSink()
    gate = _gate(sink)
    result: ReleaseDecision | None = None
    with pytest.raises(OutputReviewError):
        result = gate.decide(_passing_verdict(), reason="would-have-passed")
    assert result is None  # NO decision handed back when it could not be audited
    assert sink.calls == 1  # the write was attempted exactly once, then refused


def test_audit_failure_chains_the_underlying_cause() -> None:
    # The wrapped OutputReviewError preserves the original sink failure (traceability).
    sink = _RaisingSink()
    with pytest.raises(OutputReviewError) as ei:
        _gate(sink).decide(_failing_verdict(), reason="x")
    assert isinstance(ei.value.__cause__, RuntimeError)


# ================================================================================
# 6. Determinism — fixed injected clock => stable decided_at and equal decisions.
# ================================================================================
def test_determinism_fixed_clock_yields_stable_decided_at() -> None:
    sink = _SpySink()
    gate = _gate(sink, at=_OTHER_AT)
    a = gate.decide(_passing_verdict(), reason="r")
    b = gate.decide(_passing_verdict(), reason="r")
    assert a.decided_at == _OTHER_AT == b.decided_at
    assert a == b  # frozen models with identical fields compare equal
    assert a.model_dump() == b.model_dump()


def test_decision_uses_injected_clock_not_wall_clock() -> None:
    # decided_at is whatever the clock returns — proving now() is never consulted.
    sink = _SpySink()
    marker = datetime(1999, 12, 31, 23, 59, tzinfo=UTC)
    decision = ReleaseDecisionGate(sink=sink, clock=lambda: marker).decide(
        _passing_verdict(), reason="r"
    )
    assert decision.decided_at == marker


# ================================================================================
# 7. Protocol conformance — the spy satisfies the runtime-checkable seam.
# ================================================================================
def test_spy_sink_satisfies_protocol() -> None:
    assert isinstance(_SpySink(), ReleaseAuditSink)
    assert isinstance(_RaisingSink(), ReleaseAuditSink)


def test_non_sink_object_fails_protocol() -> None:
    # A bare object with no record() is NOT a sink (the seam is structural, not nominal).
    assert not isinstance(object(), ReleaseAuditSink)


# ================================================================================
# 8. PROPERTY — for ANY verdict, authorised IFF it passed, and outcome matches.
# ================================================================================
@st.composite
def _verdicts(draw: st.DrawFn) -> ReviewVerdict:
    n_blocking = draw(st.integers(min_value=0, max_value=3))
    n_advisory = draw(st.integers(min_value=0, max_value=3))
    findings = tuple(
        [_blocking_finding(i) for i in range(n_blocking)]
        + [_advisory_finding(100 + i) for i in range(n_advisory)]
    )
    return ReviewVerdict(artifact_ref="art-p", findings=findings, reviewed_at=_FIXED_AT)


@settings(max_examples=300)
@given(verdict=_verdicts())
def test_property_authorised_iff_passed_and_outcome_matches(verdict: ReviewVerdict) -> None:
    """For ANY verdict: authorised == passed, and the audited outcome tracks it."""
    sink = _SpySink()
    decision = _gate(sink).decide(verdict, reason="prop")
    assert decision.authorised == verdict.passed
    expected = AuditOutcome.SUCCESS if verdict.passed else AuditOutcome.DENY
    assert sink.calls[0]["outcome"] is expected


# ================================================================================
# 9. EXACT-MESSAGE pins (kill string-literal mutants). mutmut wraps every string
# literal in XX..XX, so an `in`/substring assertion passes the mutant; only a full
# `==` on the EXACT text kills it. The text is hard-coded (never imported from the
# module) so a test can't compare a mutated literal to itself. Each would FAIL if a
# single character — or the !r-quoting of the supplied/derived pair — changed.
# ================================================================================
def test_blank_reason_refusal_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as exc_info:
        ReleaseDecision(
            artifact_ref="art-1",
            final_verdict=_passing_verdict(),
            reason="   ",
            decided_at=_FIXED_AT,
        )
    assert str(exc_info.value) == (
        "ReleaseDecision artifact_ref and reason must be non-blank"
    )


def test_blank_artifact_ref_refusal_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as exc_info:
        ReleaseDecision(
            artifact_ref="  ",
            final_verdict=_passing_verdict(),
            reason="ok",
            decided_at=_FIXED_AT,
        )
    assert str(exc_info.value) == (
        "ReleaseDecision artifact_ref and reason must be non-blank"
    )


def test_false_pass_refusal_message_is_exact_true_over_failing() -> None:
    # Concrete supplied/derived pair: authorised=True over a FAILING verdict
    # (derived=False). The message must render the pair with !r => `True` / `False`.
    with pytest.raises(OutputReviewError) as exc_info:
        ReleaseDecision(
            artifact_ref="art-1",
            final_verdict=_failing_verdict(),
            reason="forced",
            decided_at=_FIXED_AT,
            authorised=True,
        )
    assert str(exc_info.value) == (
        "ReleaseDecision.authorised must equal final_verdict.passed; "
        "supplied=True, derived=False"
    )


def test_false_pass_refusal_message_is_exact_false_over_passing() -> None:
    # The symmetric pair: authorised=False over a PASSING verdict (derived=True).
    # Pins that BOTH interpolated slots track their real values, exactly.
    with pytest.raises(OutputReviewError) as exc_info:
        ReleaseDecision(
            artifact_ref="art-1",
            final_verdict=_passing_verdict(),
            reason="forced",
            decided_at=_FIXED_AT,
            authorised=False,
        )
    assert str(exc_info.value) == (
        "ReleaseDecision.authorised must equal final_verdict.passed; "
        "supplied=False, derived=True"
    )


def test_audit_failure_refusal_message_is_exact() -> None:
    sink = _RaisingSink()
    with pytest.raises(OutputReviewError) as exc_info:
        _gate(sink).decide(_passing_verdict(), reason="would-have-passed")
    assert str(exc_info.value) == (
        "release blocked: audit write failed — an unaudited release is forbidden"
    )
