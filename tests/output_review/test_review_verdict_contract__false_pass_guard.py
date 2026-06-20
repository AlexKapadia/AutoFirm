"""Teeth-tests for the ReviewVerdict FALSE-PASS GUARD (the lane's core invariant).

These prove ``passed == (no BLOCKING finding present)`` for EVERY constructible
verdict, and that no field combination, ordering, or duplicate can manufacture a
green-but-wrong verdict (CLAUDE.md §3.6; SYNTHESIS finding #6). Each test would FAIL
if the guard in :mod:`autofirm.output_review.review_verdict_contract` were wrong —
none is tautological.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

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
    """A valid finding of a given severity (synthetic, distinct locator per idx)."""
    return ReviewFinding(
        check_id=ReviewCheckId.ACCOUNTING_IDENTITY,
        severity=severity,
        defect_class=DefectClass.PURE_LOGIC,
        message="A != L + E",
        locator=f"Sheet1!B{idx}",
        expected="A=100",
        actual="L+E=99",
    )


# ---- boundary-exact cases ------------------------------------------------------


def test_zero_findings_derives_passed_true() -> None:
    v = ReviewVerdict(artifact_ref="art-1", findings=(), reviewed_at=_FIXED_AT)
    assert v.passed is True


def test_single_advisory_only_passes() -> None:
    v = ReviewVerdict(
        artifact_ref="art-1",
        findings=(_finding(CheckSeverity.ADVISORY),),
        reviewed_at=_FIXED_AT,
    )
    assert v.passed is True
    assert v.blocking_findings == ()


def test_single_blocking_derives_passed_false() -> None:
    v = ReviewVerdict(
        artifact_ref="art-1",
        findings=(_finding(CheckSeverity.BLOCKING),),
        reviewed_at=_FIXED_AT,
    )
    assert v.passed is False
    assert len(v.blocking_findings) == 1


def test_mixed_one_blocking_among_advisories_fails() -> None:
    findings = (
        _finding(CheckSeverity.ADVISORY, 1),
        _finding(CheckSeverity.BLOCKING, 2),
        _finding(CheckSeverity.ADVISORY, 3),
    )
    v = ReviewVerdict(artifact_ref="art-1", findings=findings, reviewed_at=_FIXED_AT)
    assert v.passed is False


# ---- adversarial: cannot manufacture a false pass / false fail -----------------


def test_supplied_passed_true_with_blocking_is_refused() -> None:
    # THE attack this lane exists to stop: claim PASS while a BLOCKING defect exists.
    with pytest.raises(OutputReviewError):
        ReviewVerdict(
            artifact_ref="art-1",
            findings=(_finding(CheckSeverity.BLOCKING),),
            reviewed_at=_FIXED_AT,
            passed=True,
        )


def test_supplied_passed_false_with_no_blocking_is_refused() -> None:
    # The dual: a verdict cannot claim FAIL when nothing blocks (no silent drift).
    with pytest.raises(OutputReviewError):
        ReviewVerdict(
            artifact_ref="art-1",
            findings=(_finding(CheckSeverity.ADVISORY),),
            reviewed_at=_FIXED_AT,
            passed=False,
        )


def test_supplied_passed_matching_derivation_is_accepted() -> None:
    # A correctly-supplied flag round-trips (deserialisation re-validation path).
    v = ReviewVerdict(
        artifact_ref="art-1",
        findings=(_finding(CheckSeverity.BLOCKING),),
        reviewed_at=_FIXED_AT,
        passed=False,
    )
    assert v.passed is False


def test_many_advisories_then_one_blocking_at_end_still_fails() -> None:
    # Ordering must not matter: blocking last still forces fail.
    findings = (
        *(_finding(CheckSeverity.ADVISORY, i) for i in range(20)),
        _finding(CheckSeverity.BLOCKING, 99),
    )
    with pytest.raises(OutputReviewError):
        ReviewVerdict(
            artifact_ref="art-1", findings=findings, reviewed_at=_FIXED_AT, passed=True
        )


def test_duplicate_blocking_findings_still_fail() -> None:
    dup = _finding(CheckSeverity.BLOCKING)
    v = ReviewVerdict(artifact_ref="art-1", findings=(dup, dup), reviewed_at=_FIXED_AT)
    assert v.passed is False


def test_blank_artifact_ref_refused() -> None:
    with pytest.raises(OutputReviewError):
        ReviewVerdict(artifact_ref="   ", findings=(), reviewed_at=_FIXED_AT)


# ---- PROPERTY: passed IFF no blocking, for ANY generated finding set -----------

_severities = st.sampled_from(list(CheckSeverity))


@st.composite
def _findings(draw: st.DrawFn) -> tuple[ReviewFinding, ...]:
    n = draw(st.integers(min_value=0, max_value=12))
    out = []
    for i in range(n):
        sev = draw(_severities)
        out.append(
            ReviewFinding(
                check_id=draw(st.sampled_from(list(ReviewCheckId))),
                severity=sev,
                defect_class=draw(st.sampled_from(list(DefectClass))),
                message=draw(st.text(min_size=1, max_size=20).filter(str.strip)),
                locator=f"loc-{i}-{draw(st.integers(0, 9))}",
            )
        )
    return tuple(out)


@settings(max_examples=600)
@given(findings=_findings())
def test_property_passed_iff_no_blocking(findings: tuple[ReviewFinding, ...]) -> None:
    """For ANY finding set, derived ``passed`` is True IFF no BLOCKING finding."""
    v = ReviewVerdict(artifact_ref="art-x", findings=findings, reviewed_at=_FIXED_AT)
    expected = not any(f.severity is CheckSeverity.BLOCKING for f in findings)
    assert v.passed is expected


@settings(max_examples=400)
@given(findings=_findings())
def test_property_guard_rejects_every_inverted_supplied_passed(
    findings: tuple[ReviewFinding, ...],
) -> None:
    """Supplying the WRONG ``passed`` for ANY finding set must always be refused."""
    derived = not any(f.severity is CheckSeverity.BLOCKING for f in findings)
    with pytest.raises(OutputReviewError):
        ReviewVerdict(
            artifact_ref="art-x",
            findings=findings,
            reviewed_at=_FIXED_AT,
            passed=not derived,  # the inverted (false) value — must never be accepted
        )


# ---- determinism ---------------------------------------------------------------


def test_determinism_identical_inputs_identical_verdict() -> None:
    findings = (_finding(CheckSeverity.BLOCKING, 1), _finding(CheckSeverity.ADVISORY, 2))
    a = ReviewVerdict(artifact_ref="art-1", findings=findings, reviewed_at=_FIXED_AT)
    b = ReviewVerdict(artifact_ref="art-1", findings=findings, reviewed_at=_FIXED_AT)
    assert a == b
    assert a.passed == b.passed is False
    assert a.model_dump() == b.model_dump()


# ---- immutability + closed schema (the verdict cannot be edited after the fact) -


def test_verdict_is_frozen_cannot_mutate_passed_after_construction() -> None:
    # If the verdict were not frozen, a downstream caller could flip ``passed`` to
    # True AFTER the guard ran — re-introducing the exact false pass the guard stops.
    v = ReviewVerdict(artifact_ref="art-1", findings=(), reviewed_at=_FIXED_AT)
    with pytest.raises(ValidationError):
        v.passed = False  # frozen=True forbids post-construction mutation


def test_verdict_forbids_unknown_fields() -> None:
    # extra="forbid": an unexpected field (e.g. a smuggled override) is rejected,
    # so no out-of-contract key can ride along and silently alter behaviour.
    with pytest.raises(ValidationError):
        ReviewVerdict(
            artifact_ref="art-1",
            reviewed_at=_FIXED_AT,
            smuggled_passed=True,  # not a declared field -> refused
        )


# ---- defaults: omitting findings/checks_run must mean "empty", never None -------


def test_omitted_findings_and_checks_run_default_to_empty_tuples() -> None:
    # The empty-tuple defaults are load-bearing: a None default for ``findings``
    # would crash the blocking scan, and a None ``checks_run`` would erase the
    # omission-defence audit trail. Omitting both must yield empty tuples + pass.
    v = ReviewVerdict(artifact_ref="art-1", reviewed_at=_FIXED_AT)
    assert v.findings == ()
    assert v.checks_run == ()
    assert v.passed is True


# ---- EXACT error messages (a corrupted message must not slip through) -----------


def test_blank_ref_error_message_is_exact() -> None:
    # Pin the full message byte-for-byte: a substring check would miss a mutated
    # message that merely wraps the original, so assert exact equality.
    with pytest.raises(OutputReviewError) as excinfo:
        ReviewVerdict(artifact_ref="   ", reviewed_at=_FIXED_AT)
    assert str(excinfo.value) == "ReviewVerdict artifact_ref must be non-blank"


def test_false_pass_guard_error_message_is_exact() -> None:
    # The guard's refusal message must state the invariant AND the offending values
    # exactly (supplied vs derived), so an auditor can see why the verdict was refused.
    with pytest.raises(OutputReviewError) as excinfo:
        ReviewVerdict(
            artifact_ref="art-1",
            findings=(_finding(CheckSeverity.BLOCKING),),
            reviewed_at=_FIXED_AT,
            passed=True,
        )
    assert str(excinfo.value) == (
        "ReviewVerdict.passed must equal (no BLOCKING finding present); "
        "supplied=True, derived=False"
    )
