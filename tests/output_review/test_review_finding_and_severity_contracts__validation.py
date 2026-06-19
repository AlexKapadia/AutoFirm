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
    CHECK_DEFECT_CLASSES,
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


# ---- the CANONICAL runtime map CHECK_DEFECT_CLASSES (SYNTHESIS §3, src 03) ------
# Promoted out of this test matrix into the contract module so the gate and the
# evidence showcase share ONE source of truth. These tests pin the canonical map's
# totality + validity; a wrong/partial map would FAIL them (no tautology).


def test_check_defect_classes_is_total_over_every_check_id() -> None:
    # Omission defence: EVERY closed-set ReviewCheckId must have a defect-class home;
    # a missing key would mean a check class with no detector. Totality, both ways.
    assert set(CHECK_DEFECT_CLASSES) == set(ReviewCheckId)


def test_check_defect_classes_every_value_is_nonempty_frozenset_of_valid_classes() -> None:
    valid = set(DefectClass)
    for check_id, classes in CHECK_DEFECT_CLASSES.items():
        assert isinstance(classes, frozenset), f"{check_id} value is not a frozenset"
        assert classes, f"{check_id} maps to no defect class"
        assert classes <= valid, f"{check_id} maps an unknown defect class: {classes - valid}"


def test_check_defect_classes_is_immutable() -> None:
    # The canonical map must not be mutable at runtime (a swapped class would silently
    # mis-route detection). MappingProxyType refuses item assignment.
    with pytest.raises(TypeError):
        CHECK_DEFECT_CLASSES[ReviewCheckId.FAST_LINT] = frozenset()  # type: ignore[index]


def test_eureka_residue_only_reached_by_model_advisory() -> None:
    # SYNTHESIS §4: EUREKA is the sole class the deterministic floor cannot reach;
    # only the add-only advisory layer claims it.
    reaching = {
        cid for cid, cls in CHECK_DEFECT_CLASSES.items() if DefectClass.EUREKA in cls
    }
    assert reaching == {ReviewCheckId.MODEL_ADVISORY}


def test_deterministic_floor_covers_must_block_classes() -> None:
    # SYNTHESIS §2.2/§3: the deterministic floor (every check except MODEL_ADVISORY)
    # must between them reach MECHANICAL, PURE_LOGIC and OMISSION — the must-block set.
    floor = {
        cid for cid in CHECK_DEFECT_CLASSES if cid is not ReviewCheckId.MODEL_ADVISORY
    }
    covered: set[DefectClass] = set()
    for cid in floor:
        covered |= CHECK_DEFECT_CLASSES[cid]
    assert {DefectClass.MECHANICAL, DefectClass.PURE_LOGIC, DefectClass.OMISSION} <= covered


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


# ---- EXACT error-message pins (kill string-literal XX..XX mutants) ----------------
# A substring `in` check cannot kill a string-literal mutant ("XXfooXX" still contains
# "foo"); only an exact `==` on the FULL message does. The validator raises ONE shared
# message for blank message AND blank locator — pin it from both trigger paths.

_NON_BLANK_MESSAGE = "ReviewFinding message and locator must be non-blank"


def test_blank_message_exact_error_text() -> None:
    with pytest.raises(OutputReviewError) as exc:
        _valid(message="   ")
    assert str(exc.value) == _NON_BLANK_MESSAGE


def test_blank_locator_exact_error_text() -> None:
    with pytest.raises(OutputReviewError) as exc:
        _valid(locator="")
    assert str(exc.value) == _NON_BLANK_MESSAGE


# ---- EXACT enum value strings (kill the per-member value-literal mutants) ---------
# mutmut wraps each member's value string; assert every member's `.value` exactly so a
# single altered value string FAILS here (a set-of-values check is weaker per-member).


def test_check_severity_member_values_exact() -> None:
    assert CheckSeverity.BLOCKING.value == "BLOCKING"
    assert CheckSeverity.ADVISORY.value == "ADVISORY"


def test_review_check_id_member_values_exact() -> None:
    assert ReviewCheckId.ACCOUNTING_IDENTITY.value == "ACCOUNTING_IDENTITY"
    assert ReviewCheckId.SPEC_ROUND_TRIP.value == "SPEC_ROUND_TRIP"
    assert ReviewCheckId.NUMERIC_RECOMPUTE.value == "NUMERIC_RECOMPUTE"
    assert ReviewCheckId.FILE_OPENS_CLEAN.value == "FILE_OPENS_CLEAN"
    assert ReviewCheckId.FAST_LINT.value == "FAST_LINT"
    assert ReviewCheckId.IBCS_SUCCESS.value == "IBCS_SUCCESS"
    assert ReviewCheckId.VISUAL_INTEGRITY.value == "VISUAL_INTEGRITY"
    assert ReviewCheckId.MODEL_ADVISORY.value == "MODEL_ADVISORY"


def test_defect_class_member_values_exact() -> None:
    assert DefectClass.MECHANICAL.value == "MECHANICAL"
    assert DefectClass.PURE_LOGIC.value == "PURE_LOGIC"
    assert DefectClass.EUREKA.value == "EUREKA"
    assert DefectClass.OMISSION.value == "OMISSION"


def test_enum_member_sets_are_complete_no_extra_no_missing() -> None:
    # Pin the exact membership of each closed set so an added/removed member FAILS.
    assert set(CheckSeverity) == {CheckSeverity.BLOCKING, CheckSeverity.ADVISORY}
    assert set(ReviewCheckId) == {
        ReviewCheckId.ACCOUNTING_IDENTITY,
        ReviewCheckId.SPEC_ROUND_TRIP,
        ReviewCheckId.NUMERIC_RECOMPUTE,
        ReviewCheckId.FILE_OPENS_CLEAN,
        ReviewCheckId.FAST_LINT,
        ReviewCheckId.IBCS_SUCCESS,
        ReviewCheckId.VISUAL_INTEGRITY,
        ReviewCheckId.MODEL_ADVISORY,
    }
    assert set(DefectClass) == {
        DefectClass.MECHANICAL,
        DefectClass.PURE_LOGIC,
        DefectClass.EUREKA,
        DefectClass.OMISSION,
    }


# ---- EXACT canonical map (kill per-entry mutations of CHECK_DEFECT_CLASSES) -------
# The earlier tests pin totality/validity but not the EXACT class set per key; mutmut
# could swap a value (e.g. drop OMISSION from FAST_LINT) and survive them. Pin the
# COMPLETE map, every key -> exact frozenset, so any altered entry FAILS.

_EXPECTED_CHECK_DEFECT_CLASSES = {
    ReviewCheckId.ACCOUNTING_IDENTITY: frozenset({DefectClass.PURE_LOGIC}),
    ReviewCheckId.SPEC_ROUND_TRIP: frozenset({DefectClass.MECHANICAL}),
    ReviewCheckId.NUMERIC_RECOMPUTE: frozenset({DefectClass.MECHANICAL}),
    ReviewCheckId.FILE_OPENS_CLEAN: frozenset({DefectClass.MECHANICAL}),
    ReviewCheckId.FAST_LINT: frozenset({DefectClass.MECHANICAL, DefectClass.OMISSION}),
    ReviewCheckId.IBCS_SUCCESS: frozenset({DefectClass.PURE_LOGIC}),
    ReviewCheckId.VISUAL_INTEGRITY: frozenset({DefectClass.PURE_LOGIC}),
    ReviewCheckId.MODEL_ADVISORY: frozenset({DefectClass.EUREKA}),
}


def test_check_defect_classes_equals_exact_expected_map() -> None:
    # Whole-map equality: keys AND every value frozenset must match exactly.
    assert dict(CHECK_DEFECT_CLASSES) == _EXPECTED_CHECK_DEFECT_CLASSES


@pytest.mark.parametrize(
    ("check_id", "classes"), list(_EXPECTED_CHECK_DEFECT_CLASSES.items())
)
def test_check_defect_classes_per_key_exact_frozenset(
    check_id: ReviewCheckId, classes: frozenset[DefectClass]
) -> None:
    # Per-key exact frozenset: a single swapped/added/dropped class FAILS exactly one.
    assert CHECK_DEFECT_CLASSES[check_id] == classes


def test_check_defect_classes_keys_exactly_review_check_id() -> None:
    # Totality both directions, pinned independently of the values above.
    assert set(CHECK_DEFECT_CLASSES) == set(ReviewCheckId)
