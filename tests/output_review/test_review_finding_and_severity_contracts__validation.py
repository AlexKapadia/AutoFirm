"""Teeth-tests for the finding / severity / check-id / defect-class contracts.

Prove the shared vocabulary is fail-closed (CLAUDE.md §5.6): blank message/locator
refused, unknown enum values impossible, frozen & immutable, and the Panko-Halverson
DefectClass coverage matrix is sane (every planned check maps to >= 1 defect class —
SYNTHESIS §3). No tautologies — each asserts a failure the contract must prevent.
"""

from __future__ import annotations

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


def _valid(**over: object) -> ReviewFinding:
    base: dict[str, object] = {
        "check_id": ReviewCheckId.FAST_LINT,
        "severity": CheckSeverity.BLOCKING,
        "defect_class": DefectClass.MECHANICAL,
        "message": "orphan constant in formula row",
        "locator": "Sheet1!C9",
    }
    base.update(over)
    return ReviewFinding(**base)  # type: ignore[arg-type]


def test_valid_finding_constructs() -> None:
    f = _valid(expected="=B9*C9", actual="42")
    assert f.expected == "=B9*C9"
    assert f.actual == "42"


@pytest.mark.parametrize("blank", ["", "   ", "\t\n"])
def test_blank_message_refused(blank: str) -> None:
    with pytest.raises(OutputReviewError):
        _valid(message=blank)


@pytest.mark.parametrize("blank", ["", "   ", "\t\n"])
def test_blank_locator_refused(blank: str) -> None:
    with pytest.raises(OutputReviewError):
        _valid(locator=blank)


def test_unknown_severity_value_refused() -> None:
    with pytest.raises(ValidationError):
        _valid(severity="MAYBE_BLOCKING")  # not a CheckSeverity member


def test_unknown_check_id_refused() -> None:
    with pytest.raises(ValidationError):
        _valid(check_id="MAGIC_CHECK")  # not a ReviewCheckId member


def test_unknown_defect_class_refused() -> None:
    with pytest.raises(ValidationError):
        _valid(defect_class="GREMLIN")  # not a DefectClass member


def test_finding_is_frozen() -> None:
    f = _valid()
    with pytest.raises(ValidationError):
        f.severity = CheckSeverity.ADVISORY


def test_extra_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        _valid(bogus="x")


def test_expected_actual_default_none() -> None:
    f = _valid()
    assert f.expected is None and f.actual is None


def test_severity_uses_identity_safe_members() -> None:
    # The verdict guard compares with `is`; only two genuine members must exist.
    assert set(CheckSeverity) == {CheckSeverity.BLOCKING, CheckSeverity.ADVISORY}


def test_defect_class_encodes_panko_halverson_taxonomy() -> None:
    # SYNTHESIS src 03: the four-class taxonomy must be present, exactly.
    assert {d.value for d in DefectClass} == {
        "MECHANICAL",
        "PURE_LOGIC",
        "EUREKA",
        "OMISSION",
    }


# ---- coverage matrix: every planned DETERMINISTIC check maps to >=1 class ------
# SYNTHESIS §3 maps each Panko-Halverson class to the deterministic checks that must
# kill it. EUREKA is the residue only MODEL_ADVISORY reaches. This sanity matrix
# proves no deterministic check id is left without a defect-class home.

_CHECK_TO_CLASSES: dict[ReviewCheckId, set[DefectClass]] = {
    ReviewCheckId.ACCOUNTING_IDENTITY: {DefectClass.PURE_LOGIC},
    ReviewCheckId.SPEC_ROUND_TRIP: {DefectClass.MECHANICAL, DefectClass.PURE_LOGIC},
    ReviewCheckId.NUMERIC_RECOMPUTE: {DefectClass.MECHANICAL},
    ReviewCheckId.FILE_OPENS_CLEAN: {DefectClass.MECHANICAL},
    ReviewCheckId.FAST_LINT: {DefectClass.MECHANICAL, DefectClass.OMISSION},
    ReviewCheckId.IBCS_SUCCESS: {DefectClass.PURE_LOGIC},
    ReviewCheckId.VISUAL_INTEGRITY: {DefectClass.PURE_LOGIC},
    ReviewCheckId.MODEL_ADVISORY: {DefectClass.EUREKA},
}


def test_every_check_id_maps_to_at_least_one_defect_class() -> None:
    # Every member of the closed check set must have a defect-class home (omission
    # defence: an unmapped check would mean a defect class with no detector).
    assert set(_CHECK_TO_CLASSES) == set(ReviewCheckId)
    for check_id, classes in _CHECK_TO_CLASSES.items():
        assert classes, f"{check_id} maps to no defect class"


def test_eureka_residue_only_reached_by_model_advisory() -> None:
    # SYNTHESIS §4: EUREKA is the sole class the deterministic floor cannot reach;
    # only the add-only advisory layer claims it.
    reaching = {cid for cid, cls in _CHECK_TO_CLASSES.items() if DefectClass.EUREKA in cls}
    assert reaching == {ReviewCheckId.MODEL_ADVISORY}


@settings(max_examples=200)
@given(
    sev=st.sampled_from(list(CheckSeverity)),
    cid=st.sampled_from(list(ReviewCheckId)),
    dc=st.sampled_from(list(DefectClass)),
    msg=st.text(min_size=1, max_size=40).filter(str.strip),
)
def test_property_any_valid_enum_combo_constructs(
    sev: CheckSeverity, cid: ReviewCheckId, dc: DefectClass, msg: str
) -> None:
    """Any combination of valid enum members + non-blank text constructs cleanly."""
    f = ReviewFinding(
        check_id=cid, severity=sev, defect_class=dc, message=msg, locator="L1"
    )
    assert f.check_id is cid and f.severity is sev and f.defect_class is dc
