"""Teeth-tests for IbcsSuccessRubricCheck — the IBCS notation/units floor.

These tests must FAIL if the check were wrong (CLAUDE.md §3.6) — no tautological
asserts. They prove, with boundary-exact assertions:

* a False ``has_notation`` flag yields exactly one BLOCKING/PURE_LOGIC finding located
  at that element, with the notation message — and likewise for ``has_units``;
* an element missing BOTH owned flags yields exactly two findings, distinct messages;
* a fully-compliant deck yields ``()`` — the suite would catch a check that flags a
  clean deck;
* NON-OVERLAP: an element whose ``has_overlap`` / ``has_clipping`` / ``axis_truncated``
  visual-integrity flags are set but whose owned flags are True yields ``()`` — this
  check must NEVER raise a visual-integrity defect (a different check owns those);
* fail-closed: a slide deck with no ``deck_facts`` bundle yields ONE BLOCKING finding;
* a non-SLIDE_DECK kind yields ``()`` (inapplicable);
* determinism over many repeats; Protocol conformance; and a property test that the
  finding count equals exactly the number of False owned flags across the deck.

Synthetic facts only; no network; no real PII (CLAUDE.md §5.6/§3.12).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.output_review.ibcs_success_rubric_check import IbcsSuccessRubricCheck
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
from autofirm.output_review.reviewable_artifact_facts import (
    DeckElementFacts,
    DeckStructuralFacts,
)

# Distinct, load-bearing message text the check is contractually required to emit.
# Asserting on these (not just "a finding exists") gives the units/notation tests real
# teeth — a check that swapped the two messages would fail.
_NOTATION_MESSAGE = "IBCS notation missing"
_UNITS_MESSAGE = "axis/value units unlabelled"
_ABSENT_MESSAGE = "deck facts absent — cannot verify IBCS"


def _element(
    element_id: str,
    *,
    has_notation: bool = True,
    has_units: bool = True,
    **visual_flags: bool,
) -> DeckElementFacts:
    """One synthetic deck element; defaults are fully-compliant (no defect).

    ``visual_flags`` forwards ``has_overlap`` / ``has_clipping`` / ``axis_truncated``
    (all defaulting to ``False`` in the facts model) so non-overlap tests can set the
    visual-integrity flags this check must IGNORE.
    """
    return DeckElementFacts(
        element_id=element_id,
        element_kind="BAR_CHART",
        has_notation=has_notation,
        has_units=has_units,
        **visual_flags,
    )


def _deck(*elements: DeckElementFacts) -> ReviewableArtifact:
    """A SLIDE_DECK artifact whose deck_facts holds the given elements."""
    return ReviewableArtifact(
        artifact_ref="deck-ref-1",
        kind=ArtifactKind.SLIDE_DECK,
        path=Path("/synthetic/deck.pptx"),
        deck_facts=DeckStructuralFacts(elements=elements),
    )


def _check() -> IbcsSuccessRubricCheck:
    return IbcsSuccessRubricCheck()


# --------------------------------------------------------------------------------- #
# Identity / protocol
# --------------------------------------------------------------------------------- #
def test_id_is_ibcs_success() -> None:
    assert _check().id is ReviewCheckId.IBCS_SUCCESS


def test_satisfies_review_check_protocol() -> None:
    assert isinstance(_check(), ReviewCheck)


# --------------------------------------------------------------------------------- #
# Teeth: notation defect
# --------------------------------------------------------------------------------- #
def test_missing_notation_yields_one_notation_finding() -> None:
    out = _check().run(_deck(_element("slide#1/chart#1", has_notation=False)))
    assert len(out) == 1
    (finding,) = out
    assert finding.severity is CheckSeverity.BLOCKING
    assert finding.defect_class is DefectClass.PURE_LOGIC
    assert finding.check_id is ReviewCheckId.IBCS_SUCCESS
    assert finding.locator == "slide#1/chart#1"  # points at the exact element
    assert finding.message == _NOTATION_MESSAGE
    # boundary: it is a notation defect, NOT a units defect.
    assert finding.message != _UNITS_MESSAGE


# --------------------------------------------------------------------------------- #
# Teeth: units defect
# --------------------------------------------------------------------------------- #
def test_missing_units_yields_one_units_finding() -> None:
    out = _check().run(_deck(_element("slide#2/chart#1", has_units=False)))
    assert len(out) == 1
    (finding,) = out
    assert finding.severity is CheckSeverity.BLOCKING
    assert finding.defect_class is DefectClass.PURE_LOGIC
    assert finding.locator == "slide#2/chart#1"
    assert finding.message == _UNITS_MESSAGE
    assert finding.message != _NOTATION_MESSAGE


# --------------------------------------------------------------------------------- #
# Teeth: BOTH flags missing -> exactly two distinct findings, notation before units
# --------------------------------------------------------------------------------- #
def test_missing_both_yields_two_distinct_findings_in_order() -> None:
    out = _check().run(
        _deck(_element("slide#3/chart#1", has_notation=False, has_units=False))
    )
    assert len(out) == 2
    # both located at the same element, but with the two distinct owned messages.
    assert {f.locator for f in out} == {"slide#3/chart#1"}
    assert [f.message for f in out] == [_NOTATION_MESSAGE, _UNITS_MESSAGE]
    assert len({f.message for f in out}) == 2  # distinct, not duplicated
    assert all(f.severity is CheckSeverity.BLOCKING for f in out)
    assert all(f.defect_class is DefectClass.PURE_LOGIC for f in out)


# --------------------------------------------------------------------------------- #
# Teeth: fully-compliant deck -> empty (would catch a check that flags clean decks)
# --------------------------------------------------------------------------------- #
def test_compliant_deck_yields_no_findings() -> None:
    out = _check().run(
        _deck(
            _element("slide#1/chart#1"),
            _element("slide#1/title#1"),
            _element("slide#2/chart#1"),
        )
    )
    assert out == ()


# --------------------------------------------------------------------------------- #
# Teeth: multi-element, only the bad one is flagged
# --------------------------------------------------------------------------------- #
def test_only_offending_element_flagged_among_many() -> None:
    out = _check().run(
        _deck(
            _element("good#1"),
            _element("bad#2", has_units=False),
            _element("good#3"),
        )
    )
    assert len(out) == 1
    (finding,) = out
    assert finding.locator == "bad#2"  # not good#1 / good#3
    assert finding.message == _UNITS_MESSAGE


def test_element_order_preserved_across_multiple_defects() -> None:
    out = _check().run(
        _deck(
            _element("e1", has_notation=False),
            _element("e2", has_units=False),
        )
    )
    # element order drives finding order: e1's notation defect before e2's units defect.
    assert [(f.locator, f.message) for f in out] == [
        ("e1", _NOTATION_MESSAGE),
        ("e2", _UNITS_MESSAGE),
    ]


# --------------------------------------------------------------------------------- #
# Teeth (CRITICAL non-overlap): visual-integrity flags are NOT this check's business
# --------------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "kwargs",
    [
        {"has_overlap": True},
        {"has_clipping": True},
        {"axis_truncated": True},
        {"has_overlap": True, "has_clipping": True, "axis_truncated": True},
    ],
)
def test_visual_integrity_flags_never_flagged_by_this_check(
    kwargs: dict[str, bool],
) -> None:
    # Owned flags are clean; only visual-integrity flags are set -> this check is
    # silent. A check that read has_overlap/has_clipping/axis_truncated would FAIL here.
    out = _check().run(
        _deck(_element("slide#9/chart#1", has_notation=True, has_units=True, **kwargs))
    )
    assert out == ()


def test_visual_defect_does_not_add_to_owned_defect_count() -> None:
    # An element missing notation AND carrying every visual-integrity flag still yields
    # exactly ONE finding (the notation defect) — the visual flags add nothing here.
    out = _check().run(
        _deck(
            _element(
                "slide#9/chart#1",
                has_notation=False,
                has_units=True,
                has_overlap=True,
                has_clipping=True,
                axis_truncated=True,
            )
        )
    )
    assert len(out) == 1
    assert out[0].message == _NOTATION_MESSAGE


# --------------------------------------------------------------------------------- #
# Fail-closed: absent deck_facts on a SLIDE_DECK
# --------------------------------------------------------------------------------- #
def test_absent_deck_facts_is_one_blocking_finding() -> None:
    artifact = ReviewableArtifact(
        artifact_ref="deck-no-facts",
        kind=ArtifactKind.SLIDE_DECK,
        path=Path("/synthetic/empty.pptx"),
        deck_facts=None,
    )
    out = _check().run(artifact)
    assert len(out) == 1
    (finding,) = out
    assert finding.severity is CheckSeverity.BLOCKING
    assert finding.defect_class is DefectClass.PURE_LOGIC
    assert finding.message == _ABSENT_MESSAGE
    # fail-closed locator is the artifact ref (no element to point at).
    assert finding.locator == "deck-no-facts"


# --------------------------------------------------------------------------------- #
# Inapplicable kinds -> empty tuple
# --------------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "kind", [ArtifactKind.FINANCIAL_MODEL, ArtifactKind.BUSINESS_DOCUMENT]
)
def test_non_slide_deck_kind_is_not_applicable(kind: ArtifactKind) -> None:
    # Even with deck_facts present, a non-deck kind is not this check's job.
    artifact = ReviewableArtifact(
        artifact_ref="not-a-deck",
        kind=kind,
        path=Path("/synthetic/x"),
        deck_facts=DeckStructuralFacts(
            elements=(_element("e1", has_notation=False, has_units=False),)
        ),
    )
    assert _check().run(artifact) == ()


# --------------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------------- #
def test_determinism_identical_findings_across_repeats() -> None:
    check = _check()
    artifact = _deck(
        _element("e1", has_notation=False),
        _element("e2", has_units=False),
        _element("e3"),
    )
    baseline = check.run(artifact)
    for _ in range(50):
        again = check.run(artifact)
        assert [
            (f.check_id, f.severity, f.defect_class, f.message, f.locator)
            for f in again
        ] == [
            (f.check_id, f.severity, f.defect_class, f.message, f.locator)
            for f in baseline
        ]


# --------------------------------------------------------------------------------- #
# Defect-class consistency: never raise a class this check does not own
# --------------------------------------------------------------------------------- #
def test_findings_carry_only_a_registered_defect_class() -> None:
    owned = CHECK_DEFECT_CLASSES[ReviewCheckId.IBCS_SUCCESS]
    out = _check().run(
        _deck(_element("e1", has_notation=False, has_units=False))
    )
    assert out  # there ARE findings to check (guards a vacuous pass)
    for finding in out:
        assert finding.defect_class in owned


# --------------------------------------------------------------------------------- #
# Property: finding count == number of False owned flags across the deck
# --------------------------------------------------------------------------------- #
@settings(max_examples=300)
@given(
    flags=st.lists(
        st.tuples(st.booleans(), st.booleans()),  # (has_notation, has_units) per element
        min_size=1,
        max_size=12,
    )
)
def test_property_finding_count_equals_false_owned_flags(
    flags: list[tuple[bool, bool]],
) -> None:
    elements = tuple(
        _element(f"el#{i}", has_notation=n, has_units=u)
        for i, (n, u) in enumerate(flags)
    )
    out = _check().run(_deck(*elements))

    expected_count = sum((not n) + (not u) for n, u in flags)
    assert len(out) == expected_count

    # Per-element correctness: messages for element i are exactly its False owned flags.
    by_locator: dict[str, list[str]] = {}
    for finding in out:
        by_locator.setdefault(finding.locator, []).append(finding.message)
    for i, (n, u) in enumerate(flags):
        expected_msgs: list[str] = []
        if not n:
            expected_msgs.append(_NOTATION_MESSAGE)
        if not u:
            expected_msgs.append(_UNITS_MESSAGE)
        assert by_locator.get(f"el#{i}", []) == expected_msgs
