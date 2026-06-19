"""The IBCS_SUCCESS deterministic check: every deck element carries notation + units.

What this does
--------------
Defines :class:`IbcsSuccessRubricCheck`, the P1 deterministic-floor check that holds a
slide deck to the IBCS SUCCESS notation floor: every chart/element that needs IBCS
notation actually carries it, and every value/axis is unit-labelled. It satisfies the
:class:`~autofirm.output_review.review_check_protocol.ReviewCheck` Protocol — exposing
the :class:`~autofirm.output_review.review_finding_and_severity_contracts.ReviewCheckId`
it owns and a pure, deterministic ``run`` that returns the
:class:`~autofirm.output_review.review_finding_and_severity_contracts.ReviewFinding`
tuple it raises (empty == clean).

It reads ONLY two boolean flags per element on the by-value ``deck_facts`` bundle:
``has_notation`` and ``has_units``. Each is a *requirement-satisfied* boolean the
CALLER sets — ``True`` means "IBCS notation/units present OR not required for this
element"; ``False`` means a genuine IBCS defect. The check is therefore the pure
boolean floor: any element whose owned flag is ``False`` is a defect. This keeps the
check fully general across notations and element kinds — it hard-codes no element-kind
label list, so it never overfits to a particular deck shape (CLAUDE.md §3.9).

Why it exists / where it sits
-----------------------------
``SYNTHESIS.md`` §2.2/§3 makes the deterministic floor a set of independent, pure
checks; this is the IBCS_SUCCESS member. A chart with the right structure but missing
notation/units has a wrong *value* relationship to the IBCS rubric — the
Panko-Halverson PURE_LOGIC bucket this check is registered under
(``CHECK_DEFECT_CLASSES[IBCS_SUCCESS]``). It is a pure function of the by-value
``deck_facts`` (plan §B.3) — no file IO, clock, or randomness — so the gate (P2)
composes it deterministically.

Boundary of responsibility (non-overlap)
----------------------------------------
This check owns ``has_notation`` and ``has_units`` ONLY. The layout / misleading-axis
flags on the same element (``has_overlap`` / ``has_clipping`` / ``axis_truncated``)
belong to the SEPARATE ``VISUAL_INTEGRITY`` check and are deliberately never read
here — an element flawless on notation + units returns ``()`` from this check even if
those visual-integrity flags are set, so the two checks can never shadow each other.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Fail closed on absent facts:** a SLIDE_DECK with no ``deck_facts`` bundle cannot
  be verified, so the check emits ONE BLOCKING finding rather than vacuously passing —
  an unverifiable deck is refused, never waved through.
* **Pure & deterministic:** ``run`` reads only the frozen artifact, performs no IO,
  consults no clock/RNG, and mutates nothing — the same artifact always yields the
  same ordered findings tuple (element order as given).
* **Defect-class consistency:** every finding is classified ``PURE_LOGIC``, a member
  of ``CHECK_DEFECT_CLASSES[IBCS_SUCCESS]`` — a finding can never carry a class this
  check does not own.
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

__all__ = ["IbcsSuccessRubricCheck"]

# The single defect class this check raises. PURE_LOGIC because an element missing
# IBCS notation/units has the right structure (it is a chart) but a wrong value
# relationship to the rubric (Panko-Halverson). Asserted against CHECK_DEFECT_CLASSES
# in the teeth-tests so the constant can never drift out of the registered class set.
_DEFECT_CLASS = DefectClass.PURE_LOGIC

# Message when a slide deck arrives with no structural facts to check. Fail-closed
# (CLAUDE.md §5.6): we cannot verify the rubric, so we refuse — the absence is itself
# the blocking defect.
_ABSENT_FACTS_MESSAGE = "deck facts absent — cannot verify IBCS"

# Per-defect messages. Distinct strings so a send-back can tell a notation defect from
# a units defect on the same element (machine-actionable explanation — CLAUDE.md §3.11).
_NOTATION_MISSING_MESSAGE = "IBCS notation missing"
_UNITS_MISSING_MESSAGE = "axis/value units unlabelled"


class IbcsSuccessRubricCheck:
    """Verify every deck element carries IBCS notation and unit labels.

    Implements the :class:`~autofirm.output_review.review_check_protocol.ReviewCheck`
    Protocol (runtime-checkable) for :attr:`ReviewCheckId.IBCS_SUCCESS`. The check is
    stateless — a single instance may be reused across artifacts because ``run`` holds
    no state and reads nothing but the artifact handed to it (independence, plan §B.3).

    Inputs
    ------
    ``run`` takes one
    :class:`~autofirm.output_review.reviewable_artifact_contract.ReviewableArtifact`
    and reads only its ``kind`` and (by value) the ``has_notation`` / ``has_units``
    flags of each element in ``deck_facts``.

    Outputs
    -------
    An ordered ``tuple[ReviewFinding, ...]`` (empty == clean):

    * ``kind`` is not :attr:`ArtifactKind.SLIDE_DECK` -> ``()`` (not applicable).
    * ``kind`` is a slide deck but ``deck_facts`` is ``None`` -> exactly one BLOCKING
      finding located at the artifact ref (the rubric cannot be verified — fail-closed).
    * otherwise -> for each element, in element order: one BLOCKING finding if
      ``has_notation`` is ``False`` and one if ``has_units`` is ``False`` (an element
      missing both yields exactly two distinct findings); ``()`` when every element has
      both flags ``True``.

    Failure modes
    -------------
    ``run`` raises nothing of its own: malformed facts are refused upstream at
    contract-construction time (e.g. blank ids, empty/duplicate elements). It is pure
    and deterministic — no IO, no clock, no randomness, no mutation.
    """

    @property
    def id(self) -> ReviewCheckId:
        """The closed-set id this check owns (its registry key)."""
        return ReviewCheckId.IBCS_SUCCESS

    def run(self, artifact: ReviewableArtifact) -> tuple[ReviewFinding, ...]:
        """Return the IBCS notation/units findings for ``artifact`` (empty == clean).

        See the class docstring for the full applicability ladder. The method is a
        pure function of ``artifact``: it branches on ``kind``, refuses fail-closed
        when a slide deck lacks structural facts, and otherwise walks the elements in
        order emitting one BLOCKING finding per ``False`` owned flag.
        """
        # Applicability gate: the IBCS rubric is meaningful only for a slide deck. Any
        # other kind is simply not this check's job, so it declines with an empty tuple
        # (not a defect — just inapplicable).
        if artifact.kind is not ArtifactKind.SLIDE_DECK:
            return ()

        # fail-closed: a slide deck with no structural facts cannot be verified — emit
        # one BLOCKING finding rather than vacuously pass (CLAUDE.md §5.6).
        if artifact.deck_facts is None:
            return (self._absent_facts_finding(artifact.artifact_ref),)

        # One BLOCKING finding per False owned flag, walked in element order then
        # notation-before-units within each element (deterministic). An element clean
        # on both owned flags yields nothing; an all-clean deck yields the empty tuple.
        findings: list[ReviewFinding] = []
        for element in artifact.deck_facts.elements:
            findings.extend(self._element_findings(element))
        return tuple(findings)

    @staticmethod
    def _absent_facts_finding(artifact_ref: str) -> ReviewFinding:
        """Build the BLOCKING finding for a deck that carries no structural facts.

        The locator is the artifact reference itself: there is no element to point at,
        so the whole artifact is the defect site. Fail-closed (CLAUDE.md §5.6).
        """
        return ReviewFinding(
            check_id=ReviewCheckId.IBCS_SUCCESS,
            severity=CheckSeverity.BLOCKING,
            defect_class=_DEFECT_CLASS,
            message=_ABSENT_FACTS_MESSAGE,
            locator=artifact_ref,
        )

    @staticmethod
    def _element_findings(element: DeckElementFacts) -> tuple[ReviewFinding, ...]:
        """Build the BLOCKING findings owned by this check for one element.

        Reads ONLY ``has_notation`` then ``has_units`` (never the visual-integrity
        flags, which belong to a different check). Notation is emitted before units so
        an element missing both yields two findings in a fixed, deterministic order,
        each located at the element id so a fix targets that exact element.
        """
        findings: list[ReviewFinding] = []
        # has_notation: True means present OR not required; only False is a defect.
        if not element.has_notation:
            findings.append(
                ReviewFinding(
                    check_id=ReviewCheckId.IBCS_SUCCESS,
                    severity=CheckSeverity.BLOCKING,
                    defect_class=_DEFECT_CLASS,
                    message=_NOTATION_MISSING_MESSAGE,
                    locator=element.element_id,
                )
            )
        # has_units: True means labelled OR not required; only False is a defect.
        if not element.has_units:
            findings.append(
                ReviewFinding(
                    check_id=ReviewCheckId.IBCS_SUCCESS,
                    severity=CheckSeverity.BLOCKING,
                    defect_class=_DEFECT_CLASS,
                    message=_UNITS_MISSING_MESSAGE,
                    locator=element.element_id,
                )
            )
        return tuple(findings)
