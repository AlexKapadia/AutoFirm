"""Teeth-tests for VISUAL_INTEGRITY: truncated axes, overlap, and clipping.

Prove the check has teeth (CLAUDE.md §3.6) — every assertion would FAIL if the code
were wrong:

* each of the three owned flags (``axis_truncated`` / ``has_overlap`` /
  ``has_clipping``), tripped INDEPENDENTLY, yields exactly one finding with the
  matching message + element id;
* all three tripped on one element yields exactly three findings in the FIXED order
  axis → overlap → clipping;
* a clean deck yields ``()``; multi-element decks flag only the bad element;
* NON-OVERLAP teeth: an element with ``has_notation``/``has_units`` False but all
  three visual flags False yields ``()`` — this check must NEVER read the IBCS flags
  (that is the IBCS_SUCCESS check's scope, plan §B.3);
* fail-closed: a SLIDE_DECK with ``deck_facts=None`` yields ONE BLOCKING finding;
* non-applicable kinds yield ``()``;
* determinism: N repeats are byte-identical;
* the check satisfies the runtime-checkable Protocol and every finding's class is in
  ``CHECK_DEFECT_CLASSES[VISUAL_INTEGRITY]`` so the constant can never drift.

All fixtures are synthetic; no network, no IO (CLAUDE.md §5.5).
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
from autofirm.output_review.reviewable_artifact_facts import (
    DeckElementFacts,
    DeckStructuralFacts,
)
from autofirm.output_review.visual_integrity_lint_check import VisualIntegrityLintCheck

# The exact per-flag messages the check is contracted to emit, paired with the
# attribute that triggers each. Centralised so the teeth-tests assert the EXACT
# wording (a mutated message string is caught) — never a substring.
_AXIS_MSG = "value axis misleadingly truncated / not zero-based"
_OVERLAP_MSG = "element overlaps another (layout defect)"
_CLIPPING_MSG = "content clipped/truncated"
_ABSENT_MSG = "deck facts absent — cannot verify visual integrity"


def _deck(*elements: DeckElementFacts) -> ReviewableArtifact:
    """A SLIDE_DECK artifact carrying ``elements`` (synthetic, no IO)."""
    return ReviewableArtifact(
        artifact_ref="deck-ref",
        kind=ArtifactKind.SLIDE_DECK,
        path=Path("/synthetic/deck.pptx"),
        deck_facts=DeckStructuralFacts(elements=elements),
    )


def _element(
    element_id: str = "slide#1/chart#1",
    *,
    axis_truncated: bool = False,
    has_overlap: bool = False,
    has_clipping: bool = False,
) -> DeckElementFacts:
    """One synthetic deck element with explicit visual flags (all default False).

    The IBCS flags (``has_notation`` / ``has_units``) are deliberately left at their
    contract default of False here; tests that exercise them set them inline so this
    check's non-reading of them is proven explicitly.
    """
    return DeckElementFacts(
        element_id=element_id,
        element_kind="BAR_CHART",
        axis_truncated=axis_truncated,
        has_overlap=has_overlap,
        has_clipping=has_clipping,
    )


# --------------------------------------------------------------------------------- #
# Protocol conformance + id.
# --------------------------------------------------------------------------------- #
def test_satisfies_review_check_protocol() -> None:
    """The check is a runtime-checkable ReviewCheck owning the VISUAL_INTEGRITY id."""
    check = VisualIntegrityLintCheck()
    assert isinstance(check, ReviewCheck)
    assert check.id is ReviewCheckId.VISUAL_INTEGRITY


# --------------------------------------------------------------------------------- #
# Each owned flag, independently, fires exactly one finding with the right message.
# --------------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"axis_truncated": True}, _AXIS_MSG),
        ({"has_overlap": True}, _OVERLAP_MSG),
        ({"has_clipping": True}, _CLIPPING_MSG),
    ],
)
def test_single_flag_yields_one_matching_finding(
    kwargs: dict[str, bool], message: str
) -> None:
    """One flag True (others False) -> exactly one finding, exact message + locator."""
    element = _element(element_id="slide#2/chart#7", **kwargs)
    findings = VisualIntegrityLintCheck().run(_deck(element))

    assert len(findings) == 1
    finding = findings[0]
    assert finding.message == message
    assert finding.locator == "slide#2/chart#7"
    assert finding.check_id is ReviewCheckId.VISUAL_INTEGRITY
    assert finding.severity is CheckSeverity.BLOCKING
    assert finding.defect_class is DefectClass.PURE_LOGIC


# --------------------------------------------------------------------------------- #
# All three flags on one element -> three findings in the FIXED order.
# --------------------------------------------------------------------------------- #
def test_all_three_flags_yield_three_findings_in_fixed_order() -> None:
    """axis+overlap+clipping all True -> exactly 3 findings, axis→overlap→clipping."""
    element = _element(
        element_id="slide#3/chart#1",
        axis_truncated=True,
        has_overlap=True,
        has_clipping=True,
    )
    findings = VisualIntegrityLintCheck().run(_deck(element))

    assert [f.message for f in findings] == [_AXIS_MSG, _OVERLAP_MSG, _CLIPPING_MSG]
    # Every finding points at the same element and is BLOCKING / PURE_LOGIC.
    assert all(f.locator == "slide#3/chart#1" for f in findings)
    assert all(f.severity is CheckSeverity.BLOCKING for f in findings)
    assert all(f.defect_class is DefectClass.PURE_LOGIC for f in findings)


def test_axis_and_clipping_skips_overlap_preserving_order() -> None:
    """axis+clipping True, overlap False -> exactly [axis, clipping] (no overlap)."""
    element = _element(axis_truncated=True, has_clipping=True)
    findings = VisualIntegrityLintCheck().run(_deck(element))
    assert [f.message for f in findings] == [_AXIS_MSG, _CLIPPING_MSG]


# --------------------------------------------------------------------------------- #
# Clean deck and multi-element selectivity.
# --------------------------------------------------------------------------------- #
def test_clean_deck_yields_empty_tuple() -> None:
    """Every element with all three flags False -> () (nothing to flag)."""
    deck = _deck(_element("slide#1/a"), _element("slide#1/b"), _element("slide#2/a"))
    assert VisualIntegrityLintCheck().run(deck) == ()


def test_multi_element_flags_only_the_bad_element() -> None:
    """A clean / bad / clean deck flags ONLY the bad element's id, once."""
    deck = _deck(
        _element("slide#1/clean-a"),
        _element("slide#2/bad", has_overlap=True),
        _element("slide#3/clean-b"),
    )
    findings = VisualIntegrityLintCheck().run(deck)
    assert len(findings) == 1
    assert findings[0].locator == "slide#2/bad"
    assert findings[0].message == _OVERLAP_MSG


def test_findings_emitted_in_element_order() -> None:
    """Two bad elements -> findings in element (not id-sorted) order."""
    deck = _deck(
        _element("z-first", has_clipping=True),
        _element("a-second", has_overlap=True),
    )
    findings = VisualIntegrityLintCheck().run(deck)
    assert [f.locator for f in findings] == ["z-first", "a-second"]


# --------------------------------------------------------------------------------- #
# NON-OVERLAP teeth: the IBCS flags are NEVER read by this check.
# --------------------------------------------------------------------------------- #
def test_ibcs_flags_false_but_visual_flags_clean_is_not_flagged() -> None:
    """has_notation/has_units False, visual flags False -> () (IBCS is not our scope).

    This is the binding non-overlap proof: VISUAL_INTEGRITY must NOT flag an IBCS
    defect — that belongs to the IBCS_SUCCESS check (plan §B.3). If the check ever
    read ``has_notation``/``has_units`` this deck would wrongly produce findings.
    """
    ibcs_incomplete = DeckElementFacts(
        element_id="slide#1/chart#1",
        element_kind="BAR_CHART",
        has_notation=False,
        has_units=False,
        # all three OWNED visual flags clean — nothing for VISUAL_INTEGRITY to flag.
        axis_truncated=False,
        has_overlap=False,
        has_clipping=False,
    )
    deck = _deck(ibcs_incomplete)
    assert VisualIntegrityLintCheck().run(deck) == ()


def test_ibcs_flags_do_not_alter_visual_finding_count() -> None:
    """Toggling the IBCS flags leaves the visual findings byte-identical."""
    run = VisualIntegrityLintCheck().run
    bare_element = DeckElementFacts(
        element_id="slide#1/chart#1",
        element_kind="BAR_CHART",
        has_overlap=True,
        has_notation=False,
        has_units=False,
    )
    decorated_element = DeckElementFacts(
        element_id="slide#1/chart#1",
        element_kind="BAR_CHART",
        has_overlap=True,
        has_notation=True,
        has_units=True,
    )
    bare = run(_deck(bare_element))
    decorated = run(_deck(decorated_element))
    assert bare == decorated
    assert [f.message for f in bare] == [_OVERLAP_MSG]


# --------------------------------------------------------------------------------- #
# Fail-closed: a slide deck with no facts BLOCKS.
# --------------------------------------------------------------------------------- #
def test_slide_deck_with_no_deck_facts_blocks() -> None:
    """deck_facts=None on a SLIDE_DECK -> exactly one BLOCKING finding at the ref."""
    artifact = ReviewableArtifact(
        artifact_ref="orphan-deck",
        kind=ArtifactKind.SLIDE_DECK,
        path=Path("/synthetic/empty.pptx"),
        deck_facts=None,
    )
    findings = VisualIntegrityLintCheck().run(artifact)
    assert len(findings) == 1
    assert findings[0].severity is CheckSeverity.BLOCKING
    assert findings[0].defect_class is DefectClass.PURE_LOGIC
    assert findings[0].message == _ABSENT_MSG
    assert findings[0].locator == "orphan-deck"


# --------------------------------------------------------------------------------- #
# Applicability: non-deck kinds decline.
# --------------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "kind", [ArtifactKind.FINANCIAL_MODEL, ArtifactKind.BUSINESS_DOCUMENT]
)
def test_non_deck_kind_returns_empty(kind: ArtifactKind) -> None:
    """A non-SLIDE_DECK kind is not this check's job -> () even with deck_facts None."""
    artifact = ReviewableArtifact(
        artifact_ref="not-a-deck", kind=kind, path=Path("/synthetic/x")
    )
    assert VisualIntegrityLintCheck().run(artifact) == ()


def test_non_deck_kind_ignores_present_deck_facts() -> None:
    """Even if deck_facts are populated, a non-deck kind still returns ()."""
    artifact = ReviewableArtifact(
        artifact_ref="model-with-deck-facts",
        kind=ArtifactKind.FINANCIAL_MODEL,
        path=Path("/synthetic/m.xlsx"),
        deck_facts=DeckStructuralFacts(elements=(_element(has_overlap=True),)),
    )
    assert VisualIntegrityLintCheck().run(artifact) == ()


# --------------------------------------------------------------------------------- #
# Determinism + defect-class consistency.
# --------------------------------------------------------------------------------- #
def test_determinism_across_repeats() -> None:
    """The same artifact yields byte-identical findings across many runs."""
    deck = _deck(
        _element("slide#1", axis_truncated=True, has_clipping=True),
        _element("slide#2", has_overlap=True),
    )
    check = VisualIntegrityLintCheck()
    first = check.run(deck)
    for _ in range(64):
        assert check.run(deck) == first


def test_every_finding_class_is_registered_for_the_check() -> None:
    """No finding may carry a class outside CHECK_DEFECT_CLASSES[VISUAL_INTEGRITY]."""
    deck = _deck(
        _element("e", axis_truncated=True, has_overlap=True, has_clipping=True)
    )
    allowed = CHECK_DEFECT_CLASSES[ReviewCheckId.VISUAL_INTEGRITY]
    for finding in VisualIntegrityLintCheck().run(deck):
        assert finding.defect_class in allowed


# --------------------------------------------------------------------------------- #
# Property-based: finding count equals total tripped flags across all elements,
# and every locator is a real element id (generality, not example-fit).
# --------------------------------------------------------------------------------- #
@settings(max_examples=200)
@given(
    flags=st.lists(
        st.tuples(st.booleans(), st.booleans(), st.booleans()),
        min_size=1,
        max_size=8,
    )
)
def test_finding_count_equals_total_tripped_flags(
    flags: list[tuple[bool, bool, bool]]
) -> None:
    """For any deck, #findings == sum of all True flags, and order is per-element.

    Built from invariants (not enumerated examples), so it holds for any flag mix —
    proving generality (CLAUDE.md §3.9), and would fail if the check dropped, doubled,
    or reordered any per-element finding.
    """
    elements = tuple(
        _element(
            element_id=f"slide#{i}",
            axis_truncated=axis,
            has_overlap=overlap,
            has_clipping=clip,
        )
        for i, (axis, overlap, clip) in enumerate(flags)
    )
    findings = VisualIntegrityLintCheck().run(_deck(*elements))

    expected_total = sum(sum(triple) for triple in flags)
    assert len(findings) == expected_total

    # Reconstruct the expected (locator, message) stream and assert exact equality —
    # this pins both ordering layers (element order, then axis→overlap→clipping).
    expected_stream: list[tuple[str, str]] = []
    for i, (axis, overlap, clip) in enumerate(flags):
        if axis:
            expected_stream.append((f"slide#{i}", _AXIS_MSG))
        if overlap:
            expected_stream.append((f"slide#{i}", _OVERLAP_MSG))
        if clip:
            expected_stream.append((f"slide#{i}", _CLIPPING_MSG))
    assert [(f.locator, f.message) for f in findings] == expected_stream
