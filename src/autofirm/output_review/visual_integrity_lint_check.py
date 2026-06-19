"""The VISUAL_INTEGRITY deterministic check: no misleading axes / layout defects.

What this does
--------------
Implements :class:`VisualIntegrityLintCheck`, the deterministic-floor check that
flags the three *structural* visual-integrity defects of a slide deck — a
misleadingly truncated (non-zero-based) value axis, an element overlapping another,
and clipped/truncated content. It satisfies the
:class:`~autofirm.output_review.review_check_protocol.ReviewCheck` Protocol: it
exposes the :class:`~autofirm.output_review.review_finding_and_severity_contracts.ReviewCheckId`
it owns and a pure, deterministic ``run`` returning the
:class:`~autofirm.output_review.review_finding_and_severity_contracts.ReviewFinding`
tuple it raises (empty == clean).

Scope boundary (independence — plan §B.3)
-----------------------------------------
This check owns EXACTLY three per-element flags: ``axis_truncated``,
``has_overlap``, and ``has_clipping``. It deliberately NEVER reads ``has_notation``
or ``has_units`` — those IBCS-rubric flags belong to the separate IBCS_SUCCESS
check. A deck that is IBCS-incomplete (notation/units absent) but visually sound is
clean *to this check*, so the two checks can never relax or shadow one another.

Why it exists / where it sits
-----------------------------
``SYNTHESIS.md`` §2.2/§3 makes the deterministic floor a set of independent, pure
checks; this is the VISUAL_INTEGRITY member. A truncated axis or overlapping/clipped
element has the right *structure* (a real chart element) but a wrong, misleading
*presentation* — the Panko-Halverson PURE_LOGIC bucket this check is registered under
(``CHECK_DEFECT_CLASSES[VISUAL_INTEGRITY]``). It reads only the by-value
``deck_facts`` bundle the caller populated on the
:class:`~autofirm.output_review.reviewable_artifact_contract.ReviewableArtifact`, so
it is a pure function of plain data — no IO, no clock, no randomness, no mutation.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Fail closed on missing facts:** a SLIDE_DECK carrying no ``deck_facts`` cannot be
  verified, so the check emits ONE BLOCKING finding rather than vacuously passing —
  an unverifiable deck is refused, never waved through.
* **Applicability gate:** the visual-integrity defects are meaningful only for a
  slide deck; any other kind is simply not this check's job, so it declines with an
  empty tuple (inapplicable, not a defect).
* **Deterministic, fixed ordering:** findings are emitted in element order, and
  within an element in the fixed flag order (axis → overlap → clipping), so the same
  artifact always yields the byte-identical findings tuple.
* **Defect-class consistency:** every finding is classified ``PURE_LOGIC``, a member
  of ``CHECK_DEFECT_CLASSES[VISUAL_INTEGRITY]`` — a finding can never carry a class
  this check does not own.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autofirm.output_review.review_finding_and_severity_contracts import (
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
    ReviewFinding,
)
from autofirm.output_review.reviewable_artifact_contract import ArtifactKind

if TYPE_CHECKING:
    from autofirm.output_review.reviewable_artifact_contract import ReviewableArtifact
    from autofirm.output_review.reviewable_artifact_facts import DeckElementFacts

__all__ = ["VisualIntegrityLintCheck"]

# The single defect class this check raises. PURE_LOGIC because a truncated axis or an
# overlapping/clipped element has the right structure (a real element) but a wrong,
# misleading presentation (Panko-Halverson). Asserted against CHECK_DEFECT_CLASSES in
# the teeth-tests so the constant can never drift out of the check's registered set.
_DEFECT_CLASS = DefectClass.PURE_LOGIC

# Message used when a slide deck arrives with no structural facts to check.
# Fail-closed (CLAUDE.md §5.6): we cannot verify visual integrity, so we refuse rather
# than pass — the absence itself is the blocking defect.
_ABSENT_FACTS_MESSAGE = "deck facts absent — cannot verify visual integrity"

# Per-flag messages, kept literal so a send-back reads the same wording every run.
_AXIS_TRUNCATED_MESSAGE = "value axis misleadingly truncated / not zero-based"
_OVERLAP_MESSAGE = "element overlaps another (layout defect)"
_CLIPPING_MESSAGE = "content clipped/truncated"


class VisualIntegrityLintCheck:
    """Flag truncated axes and overlapping/clipped deck elements, per element.

    Implements the :class:`~autofirm.output_review.review_check_protocol.ReviewCheck`
    Protocol (runtime-checkable) for :attr:`ReviewCheckId.VISUAL_INTEGRITY`. The check
    is stateless; a single instance may be reused across artifacts because ``run``
    holds no state and reads only the artifact it is handed (independence, plan §B.3).

    Inputs
    ------
    ``run`` takes one
    :class:`~autofirm.output_review.reviewable_artifact_contract.ReviewableArtifact`
    and reads only its ``kind`` and (by value) ``deck_facts`` — specifically the three
    flags ``axis_truncated`` / ``has_overlap`` / ``has_clipping`` on each element. It
    NEVER reads ``has_notation`` / ``has_units`` (those are the IBCS_SUCCESS check's).

    Outputs
    -------
    An ordered ``tuple[ReviewFinding, ...]`` (empty == clean):

    * ``kind`` is not :attr:`ArtifactKind.SLIDE_DECK` -> ``()`` (not applicable).
    * ``kind`` is a slide deck but ``deck_facts`` is ``None`` -> exactly one BLOCKING
      finding (visual integrity cannot be verified — fail-closed).
    * otherwise -> for each element in order, one BLOCKING finding per TRUE flag in the
      fixed order axis → overlap → clipping; ``()`` when no element trips any flag.

    Failure modes
    -------------
    ``run`` raises nothing of its own: malformed facts are refused upstream at
    contract-construction time (blank ids, empty/duplicate elements). It is pure and
    deterministic — no IO, no clock, no randomness, no mutation — so the same artifact
    always yields the byte-identical findings tuple.
    """

    @property
    def id(self) -> ReviewCheckId:
        """The closed-set id this check owns (its registry key)."""
        return ReviewCheckId.VISUAL_INTEGRITY

    def run(self, artifact: ReviewableArtifact) -> tuple[ReviewFinding, ...]:
        """Return the visual-integrity findings for ``artifact`` (empty == clean).

        See the class docstring for the full applicability ladder. The method is a
        pure function of ``artifact``: it branches on ``kind``, refuses fail-closed
        when a slide deck lacks deck facts, and otherwise walks each element in order
        emitting one finding per tripped flag in the fixed axis → overlap → clipping
        order.
        """
        # Applicability gate: visual-integrity defects are meaningful only for a slide
        # deck. Any other kind is simply not this check's job, so it declines with an
        # empty tuple (not a defect — just inapplicable).
        if artifact.kind is not ArtifactKind.SLIDE_DECK:
            return ()

        # fail-closed: a slide deck with no structural facts cannot be verified — emit
        # one BLOCKING finding rather than vacuously pass (CLAUDE.md §5.6).
        if artifact.deck_facts is None:
            return (
                ReviewFinding(
                    check_id=ReviewCheckId.VISUAL_INTEGRITY,
                    severity=CheckSeverity.BLOCKING,
                    defect_class=_DEFECT_CLASS,
                    message=_ABSENT_FACTS_MESSAGE,
                    locator=artifact.artifact_ref,
                ),
            )

        # One BLOCKING finding per tripped flag, elements in given order and flags in
        # the fixed axis → overlap → clipping order. A clean element yields nothing; a
        # deck with no tripped flags yields the empty tuple.
        findings: list[ReviewFinding] = []
        for element in artifact.deck_facts.elements:
            findings.extend(self._element_findings(element))
        return tuple(findings)

    @staticmethod
    def _element_findings(
        element: DeckElementFacts,
    ) -> tuple[ReviewFinding, ...]:
        """Build the ordered findings for one element (empty == clean element).

        Reads ONLY the three owned flags ``axis_truncated`` / ``has_overlap`` /
        ``has_clipping`` — never ``has_notation`` / ``has_units`` (IBCS_SUCCESS's
        scope). Emits in the fixed order axis → overlap → clipping so the tuple is a
        pure function of the data (determinism, CLAUDE.md §3.11). The ``locator`` is
        the element id so a fix targets that exact element.
        """
        findings: list[ReviewFinding] = []
        # Fixed order: a misleading axis is read first, then overlap, then clipping.
        # Each is an independent defect, so all three can fire for one element.
        if element.axis_truncated:
            findings.append(
                VisualIntegrityLintCheck._finding(element.element_id, _AXIS_TRUNCATED_MESSAGE)
            )
        if element.has_overlap:
            findings.append(
                VisualIntegrityLintCheck._finding(element.element_id, _OVERLAP_MESSAGE)
            )
        if element.has_clipping:
            findings.append(
                VisualIntegrityLintCheck._finding(element.element_id, _CLIPPING_MESSAGE)
            )
        return tuple(findings)

    @staticmethod
    def _finding(element_id: str, message: str) -> ReviewFinding:
        """Build one BLOCKING / PURE_LOGIC finding located at ``element_id``."""
        return ReviewFinding(
            check_id=ReviewCheckId.VISUAL_INTEGRITY,
            severity=CheckSeverity.BLOCKING,
            defect_class=_DEFECT_CLASS,
            message=message,
            locator=element_id,
        )
