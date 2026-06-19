"""Teeth-tests for SpecRoundTripCheck — every declared spec value must survive intact.

Prove (CLAUDE.md §3.6, §5.6): the check is a fail-closed, deterministic, PURE function
of the artifact's round-trip facts. None of these asserts is tautological — each pins a
specific behaviour the check would VIOLATE if it were wrong:

* an altered value, a dropped declared key, and an unexpected extra key each raise
  exactly ONE blocking finding located at the offending key, with the exact
  ``expected``/``actual`` pair;
* identical maps raise NOTHING (no false positives);
* absent facts BLOCK (never a vacuous pass) for every artifact kind;
* findings are emitted in SORTED key order, identically across runs and across dict
  insertion orders (determinism);
* a property over random maps proves: clone round-trips clean, and ANY single mutation
  (change / drop / add) fails with the mutated key as the locator.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.output_review.review_check_protocol import ReviewCheck
from autofirm.output_review.review_finding_and_severity_contracts import (
    CHECK_DEFECT_CLASSES,
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
)
from autofirm.output_review.reviewable_artifact_contract import (
    ArtifactKind,
    ReviewableArtifact,
)
from autofirm.output_review.reviewable_artifact_facts import SpecRoundTrip
from autofirm.output_review.spec_artifact_round_trip_check import SpecRoundTripCheck

_ALL_KINDS = (
    ArtifactKind.FINANCIAL_MODEL,
    ArtifactKind.SLIDE_DECK,
    ArtifactKind.BUSINESS_DOCUMENT,
)


def _artifact(
    declared: dict[str, str] | None,
    extracted: dict[str, str] | None,
    *,
    kind: ArtifactKind = ArtifactKind.FINANCIAL_MODEL,
    ref: str = "art-ref-1",
) -> ReviewableArtifact:
    """Build a synthetic artifact; ``declared=None`` omits the round-trip bundle."""
    facts = (
        None
        if declared is None or extracted is None
        else SpecRoundTrip(declared_values=declared, extracted_values=extracted)
    )
    return ReviewableArtifact(
        artifact_ref=ref, kind=kind, path=Path("/synthetic/x"), spec_round_trip=facts
    )


# ---- protocol conformance + identity -------------------------------------------


def test_satisfies_review_check_protocol() -> None:
    assert isinstance(SpecRoundTripCheck(), ReviewCheck)


def test_id_is_spec_round_trip() -> None:
    assert SpecRoundTripCheck().id is ReviewCheckId.SPEC_ROUND_TRIP


def test_declared_defect_class_is_in_the_canonical_map() -> None:
    # The class the check stamps must be a sanctioned home for SPEC_ROUND_TRIP — guards
    # against drift between the check and CHECK_DEFECT_CLASSES (SYNTHESIS §3).
    assert DefectClass.MECHANICAL in CHECK_DEFECT_CLASSES[ReviewCheckId.SPEC_ROUND_TRIP]


# ---- the clean case: no false positives ----------------------------------------


def test_identical_maps_pass_with_no_findings() -> None:
    art = _artifact({"title": "Q4", "rev": "100"}, {"title": "Q4", "rev": "100"})
    assert SpecRoundTripCheck().run(art) == ()


# ---- single-defect teeth: altered / missing / extra ----------------------------


def test_one_altered_value_fails_with_exact_expected_actual() -> None:
    art = _artifact({"title": "Q4", "rev": "100"}, {"title": "Q4", "rev": "999"})
    findings = SpecRoundTripCheck().run(art)
    assert len(findings) == 1
    f = findings[0]
    assert f.locator == "rev"
    assert f.expected == "100"
    assert f.actual == "999"
    assert f.severity is CheckSeverity.BLOCKING
    assert f.defect_class is DefectClass.MECHANICAL
    assert f.check_id is ReviewCheckId.SPEC_ROUND_TRIP


def test_one_missing_declared_key_fails_with_absent_actual() -> None:
    # "rev" was declared by the spec but never made it into the artifact.
    art = _artifact({"title": "Q4", "rev": "100"}, {"title": "Q4"})
    findings = SpecRoundTripCheck().run(art)
    assert len(findings) == 1
    assert findings[0].locator == "rev"
    assert findings[0].expected == "100"
    assert findings[0].actual == "<absent>"


def test_one_extra_extracted_key_fails_with_absent_expected() -> None:
    # The artifact carries "ghost" which the spec never declared.
    art = _artifact({"title": "Q4"}, {"title": "Q4", "ghost": "x"})
    findings = SpecRoundTripCheck().run(art)
    assert len(findings) == 1
    assert findings[0].locator == "ghost"
    assert findings[0].expected == "<absent>"
    assert findings[0].actual == "x"


def test_absent_value_sentinel_is_not_confused_with_a_real_value() -> None:
    # A declared value that literally differs must still report the REAL actual, never
    # the sentinel — proves the sentinel only marks genuine absence.
    art = _artifact({"k": "<absent>"}, {"k": "real"})
    f = SpecRoundTripCheck().run(art)[0]
    assert f.expected == "<absent>"  # the real declared string, which happens to match
    assert f.actual == "real"


# ---- absent facts BLOCK for every kind (fail-closed) ---------------------------


@pytest.mark.parametrize("kind", _ALL_KINDS)
def test_absent_facts_block_for_every_kind(kind: ArtifactKind) -> None:
    art = _artifact(None, None, kind=kind, ref="the-ref")
    findings = SpecRoundTripCheck().run(art)
    assert len(findings) == 1
    f = findings[0]
    assert f.severity is CheckSeverity.BLOCKING
    assert f.defect_class is DefectClass.MECHANICAL
    assert f.locator == "the-ref"  # located at the artifact, not a spec key
    assert f.message == "spec round-trip facts absent — cannot verify"


@pytest.mark.parametrize("kind", _ALL_KINDS)
def test_check_applies_and_passes_clean_bundle_for_every_kind(
    kind: ArtifactKind,
) -> None:
    # The check declines NO kind — a clean bundle passes for model, deck, and document.
    art = _artifact({"k": "v"}, {"k": "v"}, kind=kind)
    assert SpecRoundTripCheck().run(art) == ()


# ---- multiple defects: one finding each, sorted by key -------------------------


def test_multiple_defects_emit_one_each_sorted_by_key() -> None:
    declared = {"alpha": "1", "beta": "2", "gamma": "3"}
    # alpha altered, beta dropped, delta is an unexpected extra; gamma is clean.
    extracted = {"alpha": "9", "gamma": "3", "delta": "x"}
    findings = SpecRoundTripCheck().run(_artifact(declared, extracted))
    locators = [f.locator for f in findings]
    assert locators == ["alpha", "beta", "delta"]  # sorted union of offending keys
    assert all(f.severity is CheckSeverity.BLOCKING for f in findings)
    # gamma round-tripped — it must NOT appear.
    assert "gamma" not in locators


# ---- determinism: identical output regardless of insertion order ---------------


def test_findings_are_identical_across_insertion_orders_and_repeats() -> None:
    check = SpecRoundTripCheck()
    declared_a = {"z": "1", "a": "2", "m": "9"}
    extracted_a = {"z": "X", "a": "2", "m": "Y"}  # z and m altered
    # Same maps, opposite insertion order.
    declared_b = {"m": "9", "a": "2", "z": "1"}
    extracted_b = {"m": "Y", "a": "2", "z": "X"}
    out_a = check.run(_artifact(declared_a, extracted_a))
    out_b = check.run(_artifact(declared_b, extracted_b))
    assert out_a == out_b
    assert [f.locator for f in out_a] == ["m", "z"]  # sorted, stable
    # Re-running the same artifact yields the byte-identical tuple (purity).
    art = _artifact(declared_a, extracted_a)
    assert check.run(art) == check.run(art) == out_a


# ---- PROPERTY: clone round-trips clean; any single mutation fails ---------------

_KEY = st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=1, max_size=6)
_VALUE = st.text(max_size=8)
_MAPS = st.dictionaries(keys=_KEY, values=_VALUE, min_size=2, max_size=8)


@settings(max_examples=400)
@given(declared=_MAPS, data=st.data())
def test_property_clone_passes_and_single_mutation_fails(
    declared: dict[str, str], data: st.DataObject
) -> None:
    """For any declared map: an exact clone passes; one mutation fails at that key."""
    check = SpecRoundTripCheck()

    # An exact re-read of the spec must round-trip with ZERO findings.
    assert check.run(_artifact(declared, dict(declared))) == ()

    kind = data.draw(st.sampled_from(["change", "drop", "add"]))
    extracted = dict(declared)
    keys = sorted(declared)

    if kind == "change":
        target = data.draw(st.sampled_from(keys))
        extracted[target] = declared[target] + "MUT"  # guaranteed-different value
    elif kind == "drop":
        target = data.draw(st.sampled_from(keys))  # min_size=2 keeps extracted non-empty
        del extracted[target]
    else:  # add an extra key the spec never declared
        target = data.draw(_KEY.filter(lambda k: k not in declared))
        extracted[target] = "extra"

    findings = check.run(_artifact(declared, extracted))
    assert len(findings) == 1
    assert findings[0].locator == target
    assert findings[0].severity is CheckSeverity.BLOCKING
    assert findings[0].defect_class is DefectClass.MECHANICAL
