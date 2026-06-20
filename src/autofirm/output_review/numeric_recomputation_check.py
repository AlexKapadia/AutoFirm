"""NUMERIC_RECOMPUTE deterministic check: declared figures must equal recomputed.

What this does
--------------
Defines :class:`NumericRecomputationCheck`, the deterministic-floor check that
guards the MECHANICAL "hard-coded constant where a formula belongs / stale cached
value" defect class for financial models. For each numeric claim the caller has
populated, it asserts the value the artifact *declares* (the cached/written figure)
equals the value the caller *recomputed independently* — EXACT to the unit
(:class:`~decimal.Decimal`, never float; CLAUDE.md §3.11). Any mismatch is one
BLOCKING finding locating the offending claim by label; a claim whose recomputed
and declared values agree raises nothing.

Why it exists / where it sits
-----------------------------
``docs/research/B16-output-review-and-verification/SYNTHESIS.md`` §2.2/§3 makes the
deterministic floor a pure function of by-value facts: the canonical defence against
a builder writing a stale constant (the spreadsheet-error MECHANICAL class,
Panko-Halverson, SYNTHESIS src 03) is to recompute the figure independently and
compare. This check is exactly that comparison, implemented as an independent, PURE
:class:`~autofirm.output_review.review_check_protocol.ReviewCheck` (plan §B.3): it
reads only the artifact, never another check's findings, and the same artifact always
yields the same findings (determinism is mandatory — CLAUDE.md §3.11).

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Fail closed on absent facts:** if the artifact is a financial model but its
  ``numeric_claims`` bundle is ``None``, the check refuses with one BLOCKING finding
  ("cannot verify") rather than vacuously passing — a missing input never reads as a
  clean result. (Non-financial kinds are out of scope and correctly decline.)
* **Exact, never approximate:** equality is ``Decimal == Decimal`` to the unit; the
  upstream fact contract already forbids ``float`` at the boundary, so no drift can
  enter. A single off-by-0.01 figure is a BLOCKING defect, not a rounding tolerance.
* **Self-explaining findings:** every finding carries the claim label as ``locator``
  and the exact ``recomputed=…`` / ``declared=…`` pair, so a send-back targets the
  one wrong figure (CLAUDE.md §3.11 explain-every-decision), never a blind retry.
"""

from __future__ import annotations

from autofirm.output_review.review_finding_and_severity_contracts import (
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
    ReviewFinding,
)
from autofirm.output_review.reviewable_artifact_contract import (
    ArtifactKind,
    ReviewableArtifact,
)

__all__ = ["NumericRecomputationCheck"]


class NumericRecomputationCheck:
    """Recompute-and-compare check for declared numeric figures (NUMERIC_RECOMPUTE).

    Implements the runtime-checkable
    :class:`~autofirm.output_review.review_check_protocol.ReviewCheck` Protocol. The
    check is stateless, PURE, and DETERMINISTIC: ``run`` reads only the artifact and
    returns the findings it raises (empty tuple == every claim agrees), so verdicts
    are reproducible (CLAUDE.md §3.11).

    Failure modes
    -------------
    Returns a single BLOCKING finding when the artifact is a financial model but its
    numeric-claim facts are absent (fail-closed — CLAUDE.md §5.6), and one BLOCKING
    finding per claim whose declared value differs from its recomputed value.
    """

    @property
    def id(self) -> ReviewCheckId:
        """The closed-set id this check owns (its registry key)."""
        return ReviewCheckId.NUMERIC_RECOMPUTE

    def run(self, artifact: ReviewableArtifact) -> tuple[ReviewFinding, ...]:
        """Compare every declared figure with its independent recomputation.

        Inputs
        ------
        ``artifact`` — the by-value :class:`ReviewableArtifact`; only ``kind``,
        ``numeric_claims`` and (for the fail-closed finding) ``artifact_ref`` are read.

        Outputs
        -------
        A tuple of :class:`ReviewFinding`, in claim order, one BLOCKING finding per
        mismatched claim. Empty when the kind is out of scope or every claim agrees.

        Failure modes
        -------------
        One BLOCKING finding (``locator=artifact.artifact_ref``) when the artifact is a
        financial model with no ``numeric_claims`` bundle — refuse, do not vacuously
        pass (fail-closed — CLAUDE.md §5.6).
        """
        # Out of scope: numeric recomputation only applies to financial models; a deck
        # or document carries no recomputable figures, so this check declines cleanly.
        if artifact.kind is not ArtifactKind.FINANCIAL_MODEL:
            return ()

        claim_set = artifact.numeric_claims
        if claim_set is None:
            # fail-closed: a financial model with no numeric-claim facts cannot be
            # verified -- block rather than let an unverifiable model read as clean.
            return (
                ReviewFinding(
                    check_id=ReviewCheckId.NUMERIC_RECOMPUTE,
                    severity=CheckSeverity.BLOCKING,
                    defect_class=DefectClass.MECHANICAL,
                    message="numeric-claim facts absent — cannot verify",
                    locator=artifact.artifact_ref,
                ),
            )

        # Exact-to-the-unit comparison per claim, preserving the caller's claim order
        # so a send-back lists defects in the order the artifact presents them.
        findings: list[ReviewFinding] = []
        for claim in claim_set.claims:
            if claim.declared_value != claim.recomputed_value:
                findings.append(
                    ReviewFinding(
                        check_id=ReviewCheckId.NUMERIC_RECOMPUTE,
                        severity=CheckSeverity.BLOCKING,
                        defect_class=DefectClass.MECHANICAL,
                        message=(
                            "declared figure does not match independent "
                            "recomputation (exact to the unit)"
                        ),
                        locator=claim.label,
                        expected=f"recomputed={claim.recomputed_value}",
                        actual=f"declared={claim.declared_value}",
                    )
                )
        return tuple(findings)
