"""Teeth-tests for build_correction_send_back — BLOCKING-only, never a clean artifact.

These prove the send-back builder (a) carries EXACTLY the verdict's blocking
findings (advisory findings excluded), (b) refuses fail-closed to send back a
PASSING verdict, and (c) preserves the attempt number, so regeneration is targeted
not blind (CLAUDE.md §3.6 + §5.6). They also pin the :class:`CorrectionSendBack`
construction guards (empty / non-blocking findings refused) and add a hypothesis
property that the carried set always equals the blocking subset for any mix. Each
test would FAIL if the builder leaked advisories, fabricated an empty send-back, or
accepted a clean verdict — none is tautological.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.output_review.correction_loop_state import CorrectionSendBack
from autofirm.output_review.correction_send_back_builder import (
    build_correction_send_back,
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


def _verdict(*findings: ReviewFinding) -> ReviewVerdict:
    return ReviewVerdict(
        artifact_ref="art-7", findings=findings, reviewed_at=_FIXED_AT
    )


# ---- failing verdict -> send-back carries EXACTLY the blocking findings ---------


def test_failing_verdict_yields_send_back_with_exact_blocking_findings() -> None:
    blocking = _finding(CheckSeverity.BLOCKING, 1)
    verdict = _verdict(blocking)
    sent = build_correction_send_back(verdict, attempt=2)
    assert isinstance(sent, CorrectionSendBack)
    assert sent.blocking_findings == (blocking,)  # EXACTLY the verdict's blocking set
    assert sent.artifact_ref == "art-7"
    assert sent.attempt == 2  # attempt preserved verbatim


def test_mixed_findings_send_back_drops_advisory_keeps_blocking() -> None:
    adv1 = _finding(CheckSeverity.ADVISORY, 1)
    block = _finding(CheckSeverity.BLOCKING, 2)
    adv2 = _finding(CheckSeverity.ADVISORY, 3)
    verdict = _verdict(adv1, block, adv2)
    sent = build_correction_send_back(verdict, attempt=1)
    # ONLY the blocking finding survives — advisories never justify a regeneration.
    assert sent.blocking_findings == (block,)
    assert adv1 not in sent.blocking_findings
    assert adv2 not in sent.blocking_findings


def test_multiple_blocking_all_carried_in_order() -> None:
    b1 = _finding(CheckSeverity.BLOCKING, 1)
    b2 = _finding(CheckSeverity.BLOCKING, 2)
    verdict = _verdict(b1, _finding(CheckSeverity.ADVISORY, 3), b2)
    sent = build_correction_send_back(verdict, attempt=3)
    assert sent.blocking_findings == (b1, b2)


# ---- passing verdict -> refused fail-closed ------------------------------------


def test_passing_verdict_with_no_findings_refused() -> None:
    # You never send back a clean artifact — nothing to correct.
    with pytest.raises(OutputReviewError):
        build_correction_send_back(_verdict(), attempt=1)


def test_passing_verdict_with_only_advisory_refused() -> None:
    # Advisory-only verdict still PASSES, so a send-back is meaningless -> refused.
    advisory_only = _verdict(_finding(CheckSeverity.ADVISORY, 1))
    assert advisory_only.passed is True
    with pytest.raises(OutputReviewError):
        build_correction_send_back(advisory_only, attempt=1)


# ---- CorrectionSendBack construction guards (fail-closed) -----------------------


def test_send_back_empty_findings_refused() -> None:
    with pytest.raises(OutputReviewError):
        CorrectionSendBack(artifact_ref="art-1", blocking_findings=(), attempt=1)


def test_send_back_with_advisory_finding_refused() -> None:
    # Any non-BLOCKING member is refused — the payload must be wholly blocking.
    with pytest.raises(OutputReviewError):
        CorrectionSendBack(
            artifact_ref="art-1",
            blocking_findings=(_finding(CheckSeverity.ADVISORY),),
            attempt=1,
        )


def test_send_back_with_mixed_findings_refused() -> None:
    with pytest.raises(OutputReviewError):
        CorrectionSendBack(
            artifact_ref="art-1",
            blocking_findings=(
                _finding(CheckSeverity.BLOCKING, 1),
                _finding(CheckSeverity.ADVISORY, 2),
            ),
            attempt=1,
        )


@pytest.mark.parametrize("bad", [0, -1])
def test_send_back_sub_one_attempt_refused(bad: int) -> None:
    with pytest.raises(OutputReviewError):
        CorrectionSendBack(
            artifact_ref="art-1",
            blocking_findings=(_finding(CheckSeverity.BLOCKING),),
            attempt=bad,
        )


def test_send_back_blank_ref_refused() -> None:
    with pytest.raises(OutputReviewError):
        CorrectionSendBack(
            artifact_ref="  ",
            blocking_findings=(_finding(CheckSeverity.BLOCKING),),
            attempt=1,
        )


def test_send_back_is_frozen() -> None:
    sent = CorrectionSendBack(
        artifact_ref="art-1",
        blocking_findings=(_finding(CheckSeverity.BLOCKING),),
        attempt=1,
    )
    with pytest.raises(ValidationError):  # pydantic frozen model rejects mutation
        sent.attempt = 2  # type: ignore[misc]


# ---- determinism ---------------------------------------------------------------


def test_determinism_identical_inputs_identical_send_back() -> None:
    verdict = _verdict(_finding(CheckSeverity.BLOCKING, 1))
    a = build_correction_send_back(verdict, attempt=2)
    b = build_correction_send_back(verdict, attempt=2)
    assert a == b
    assert a.model_dump() == b.model_dump()


# ---- PROPERTY: carried set == blocking subset, for ANY finding mix --------------

_severities = st.sampled_from(list(CheckSeverity))


@st.composite
def _findings_with_at_least_one_blocking(draw: st.DrawFn) -> tuple[ReviewFinding, ...]:
    """A finding tuple guaranteed to contain >=1 BLOCKING (so the verdict fails)."""
    n = draw(st.integers(min_value=0, max_value=8))
    out = [
        _finding(draw(_severities), i) for i in range(n)
    ]
    # Guarantee at least one blocking so verdict.passed is False (builder accepts it).
    out.append(_finding(CheckSeverity.BLOCKING, 500 + draw(st.integers(0, 99))))
    return tuple(out)


@settings(max_examples=300)
@given(findings=_findings_with_at_least_one_blocking())
def test_property_send_back_carries_exactly_blocking_subset(
    findings: tuple[ReviewFinding, ...],
) -> None:
    """For ANY failing verdict, the send-back == its blocking subset, attempt kept."""
    verdict = _verdict(*findings)
    assert verdict.passed is False
    sent = build_correction_send_back(verdict, attempt=4)
    expected = tuple(f for f in findings if f.severity is CheckSeverity.BLOCKING)
    assert sent.blocking_findings == expected
    assert all(f.severity is CheckSeverity.BLOCKING for f in sent.blocking_findings)
    assert sent.attempt == 4
