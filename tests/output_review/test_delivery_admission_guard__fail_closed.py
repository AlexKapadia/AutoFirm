"""Teeth-tests for the DELIVERY ADMISSION GUARD (the load-bearing seam check).

These prove the four refusals and the one admission that make the review gate
load-bearing at a delivery seam — each would FAIL if the guard were wrong, none is
tautological:

1. ``None`` decision is refused (no review proof — fail-closed, CLAUDE.md §5.6).
2. an UNAUTHORISED decision (built over a FAILING verdict so ``authorised`` is
   False) is refused — a blocked artifact cannot be smuggled through.
3. an authorised decision whose ``artifact_ref`` does not match the expected one is
   refused (the ref-swap hole: one valid release replayed for another artifact).
4. an authorised + ref-matching decision is ADMITTED (no raise) — the happy path.
5. with no ``expected_artifact_ref`` (the default), an authorised decision is
   admitted on authorisation alone — pinning the ``and`` in the ref check.

Exact-message pins kill the string-literal mutants (mutmut wraps every literal, so
only a full ``==`` on the hard-coded text — never imported from the module — fails
the mutant). All inputs are synthetic; no network; the clock is injected.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.output_review.delivery_admission_guard import require_authorised_release
from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.release_decision_gate import ReleaseDecision
from autofirm.output_review.review_finding_and_severity_contracts import (
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
    ReviewFinding,
)
from autofirm.output_review.review_verdict_contract import ReviewVerdict

_FIXED_AT = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)  # injected clock — never now()


def _blocking_finding() -> ReviewFinding:
    """One BLOCKING finding — forces ``passed`` False, hence ``authorised`` False."""
    return ReviewFinding(
        check_id=ReviewCheckId.ACCOUNTING_IDENTITY,
        severity=CheckSeverity.BLOCKING,
        defect_class=DefectClass.PURE_LOGIC,
        message="A != L + E",
        locator="Sheet1!B2",
        expected="A=100",
        actual="L+E=99",
    )


def _authorised(ref: str = "art-1") -> ReleaseDecision:
    """An authorised release (no blocking finding => passed => authorised)."""
    verdict = ReviewVerdict(artifact_ref=ref, findings=(), reviewed_at=_FIXED_AT)
    return ReleaseDecision(
        artifact_ref=ref, final_verdict=verdict, reason="green", decided_at=_FIXED_AT
    )


def _unauthorised(ref: str = "art-1") -> ReleaseDecision:
    """A blocked release (a BLOCKING finding => passed False => authorised False)."""
    verdict = ReviewVerdict(
        artifact_ref=ref, findings=(_blocking_finding(),), reviewed_at=_FIXED_AT
    )
    return ReleaseDecision(
        artifact_ref=ref, final_verdict=verdict, reason="blocked", decided_at=_FIXED_AT
    )


# ================================================================================
# 1. None decision -> refused (fail-closed: absence of proof is not proof).
# ================================================================================
def test_none_decision_is_refused() -> None:
    with pytest.raises(OutputReviewError):
        require_authorised_release(None, expected_artifact_ref="art-1")


def test_none_decision_is_refused_even_without_expected_ref() -> None:
    # The None refusal must fire BEFORE (and independently of) the ref binding.
    with pytest.raises(OutputReviewError):
        require_authorised_release(None)


# ================================================================================
# 2. Unauthorised decision -> refused (a blocked artifact cannot pass the seam).
# ================================================================================
def test_unauthorised_decision_is_refused() -> None:
    decision = _unauthorised("art-9")
    assert decision.authorised is False  # precondition: the verdict did NOT pass
    with pytest.raises(OutputReviewError):
        require_authorised_release(decision, expected_artifact_ref="art-9")


# ================================================================================
# 3. Ref mismatch -> refused (the ref-swap hole: a valid release for ANOTHER art).
# ================================================================================
def test_authorised_but_ref_mismatch_is_refused() -> None:
    decision = _authorised("art-a")  # authorises art-a ...
    with pytest.raises(OutputReviewError):
        require_authorised_release(decision, expected_artifact_ref="art-b")  # ... not art-b


# ================================================================================
# 4. Authorised + matching ref -> ADMITTED (no raise). The happy path.
# ================================================================================
def test_authorised_and_matching_ref_is_admitted() -> None:
    decision = _authorised("art-7")
    # Must NOT raise; returns None.
    assert require_authorised_release(decision, expected_artifact_ref="art-7") is None


# ================================================================================
# 5. Authorised + no expected ref (default) -> ADMITTED on authorisation alone.
#    Pins the ``and`` (an ``or`` would refuse here) and the ``= None`` default.
# ================================================================================
def test_authorised_with_no_expected_ref_is_admitted() -> None:
    assert require_authorised_release(_authorised("art-7")) is None


def test_authorised_with_explicit_none_expected_ref_is_admitted() -> None:
    assert require_authorised_release(_authorised("art-7"), expected_artifact_ref=None) is None


# ================================================================================
# 6. EXACT-MESSAGE pins (kill string-literal mutants — full == on hard-coded text).
# ================================================================================
def test_none_refusal_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as ei:
        require_authorised_release(None, expected_artifact_ref="art-1")
    assert str(ei.value) == (
        "delivery refused: no ReleaseDecision supplied — an authorised release "
        "is required before filing"
    )


def test_unauthorised_refusal_message_is_exact() -> None:
    with pytest.raises(OutputReviewError) as ei:
        require_authorised_release(_unauthorised("art-9"), expected_artifact_ref="art-9")
    assert str(ei.value) == (
        "delivery refused: ReleaseDecision is not authorised — the review "
        "verdict did not pass"
    )


def test_ref_mismatch_message_is_exact_with_both_refs_quoted() -> None:
    # Concrete pair pins BOTH interpolated slots (!r => single-quoted) so a mutant
    # that swaps/drops either ref, or alters the literal, is killed.
    with pytest.raises(OutputReviewError) as ei:
        require_authorised_release(_authorised("art-a"), expected_artifact_ref="art-b")
    assert str(ei.value) == (
        "delivery refused: ReleaseDecision authorises 'art-a', "
        "not the artifact being filed 'art-b'"
    )


def test_ref_mismatch_message_tracks_a_different_pair() -> None:
    # A second distinct pair proves the message tracks the real values, not a frozen
    # constant: both the authorised ref and the expected ref must appear, exactly.
    with pytest.raises(OutputReviewError) as ei:
        require_authorised_release(_authorised("doc-x@v3"), expected_artifact_ref="doc-y@v1")
    assert str(ei.value) == (
        "delivery refused: ReleaseDecision authorises 'doc-x@v3', "
        "not the artifact being filed 'doc-y@v1'"
    )


# ================================================================================
# 7. PROPERTY — admitted IFF authorised AND (expected is None OR refs match).
# ================================================================================
@st.composite
def _cases(draw: st.DrawFn) -> tuple[ReleaseDecision, str | None, bool]:
    ref = draw(st.sampled_from(["art-1", "art-2", "doc@v1"]))
    authorised = draw(st.booleans())
    decision = _authorised(ref) if authorised else _unauthorised(ref)
    expected = draw(st.sampled_from([None, "art-1", "art-2", "doc@v1"]))
    should_admit = authorised and (expected is None or ref == expected)
    return decision, expected, should_admit


@settings(max_examples=300)
@given(case=_cases())
def test_property_admit_iff_authorised_and_ref_binds(
    case: tuple[ReleaseDecision, str | None, bool],
) -> None:
    decision, expected, should_admit = case
    if should_admit:
        assert require_authorised_release(decision, expected_artifact_ref=expected) is None
    else:
        with pytest.raises(OutputReviewError):
            require_authorised_release(decision, expected_artifact_ref=expected)
