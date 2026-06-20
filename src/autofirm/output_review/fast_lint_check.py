"""FAST_LINT: the deterministic spreadsheet-model structural-lint floor check.

What this does
--------------
Implements :class:`FastLintCheck`, the deterministic-floor check that lints a
financial model's structural facts (the by-value ``ModelLintFacts`` bundle) and
raises one BLOCKING ``ReviewFinding`` per detected defect. It covers the two
FAST_LINT defect classes
(``CHECK_DEFECT_CLASSES[FAST_LINT] == {MECHANICAL, OMISSION}``):

* **MECHANICAL — orphan constants:** each cell in ``model_lint.orphan_constant_cells``
  holds a hard-coded constant where a formula belongs (Panko-Halverson MECHANICAL).
* **MECHANICAL — inconsistent rows:** each row whose ``formula_consistent`` is
  ``False`` breaks the FAST/ICAEW row-consistency rule.
* **OMISSION — missing line-items:** each name in ``expected_line_items`` absent from
  ``present_line_items`` is a completeness omission.

Why it exists / where it sits
-----------------------------
``SYNTHESIS.md`` §2.2/§3 makes the deterministic floor a set of independent, PURE
functions over by-value facts. This is the FAST_LINT member of that floor: handed
only a :class:`~autofirm.output_review.reviewable_artifact_contract.ReviewableArtifact`,
it returns the findings it raises (empty tuple == clean) and consults no other check
(independence — plan §B.3). It satisfies the runtime-checkable
:class:`~autofirm.output_review.review_check_protocol.ReviewCheck` Protocol so the
gate composes it through the registry.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Fail closed on absent facts:** if the artifact is a financial model but its
  ``model_lint`` bundle is ``None``, the check cannot verify the model, so it refuses
  with ONE BLOCKING OMISSION finding rather than waving the model through (a missing
  fact bundle must never read as "clean").
* **Pure & deterministic:** ``run`` reads only the frozen by-value artifact and never
  mutates it; findings are emitted in a fixed order (orphans in given order, rows in
  given order, missing items in ``sorted()`` order — a ``frozenset`` has no intrinsic
  order) so identical input always yields identical output (CLAUDE.md §3.11).
* **Every finding self-explains:** each carries an exact ``locator`` (cell / row /
  item) and a human-readable ``message`` so a send-back is machine-actionable.
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

__all__ = ["FastLintCheck"]

# Stable defect messages — promoted to module constants so the exact wording is a
# single source of truth (tests assert against these, evidence reports reuse them).
_ORPHAN_MESSAGE = "hard-coded constant where a formula belongs"
_ROW_MESSAGE = "row formula inconsistent"
_MISSING_MESSAGE = "required line-item/statement missing"
_ABSENT_FACTS_MESSAGE = "FAST lint facts absent — cannot verify"


class FastLintCheck:
    """Deterministic FAST_LINT floor check over a financial model's lint facts.

    Implements the :class:`~autofirm.output_review.review_check_protocol.ReviewCheck`
    Protocol. PURE and DETERMINISTIC: ``run`` is a function of the artifact alone.

    Applicability / behaviour
    -------------------------
    * Non-``FINANCIAL_MODEL`` artifact -> ``()`` (the check does not apply).
    * ``FINANCIAL_MODEL`` with ``model_lint is None`` -> ONE BLOCKING OMISSION finding
      (fail-closed: absent facts cannot be verified).
    * Otherwise -> one BLOCKING finding per defect, grouped deterministically as
      orphan constants (MECHANICAL), then inconsistent rows (MECHANICAL), then missing
      line-items (OMISSION, ``sorted``). ``()`` iff the model is fully clean.
    """

    @property
    def id(self) -> ReviewCheckId:
        """The closed-set id this check owns (its registry key)."""
        return ReviewCheckId.FAST_LINT

    def run(self, artifact: ReviewableArtifact) -> tuple[ReviewFinding, ...]:
        """Lint ``artifact``'s model facts; return findings (empty tuple == clean)."""
        # Not a spreadsheet model -> this check has nothing to say (no false defect).
        if artifact.kind is not ArtifactKind.FINANCIAL_MODEL:
            return ()

        facts = artifact.model_lint
        if facts is None:
            # fail-closed: a financial model with no lint facts cannot be verified,
            # so refuse it as a blocking omission rather than read absence as clean.
            return (
                ReviewFinding(
                    check_id=ReviewCheckId.FAST_LINT,
                    severity=CheckSeverity.BLOCKING,
                    defect_class=DefectClass.OMISSION,
                    message=_ABSENT_FACTS_MESSAGE,
                    locator=artifact.artifact_ref,
                ),
            )

        findings: list[ReviewFinding] = []

        # MECHANICAL — orphan constants, in the caller-given tuple order (determinism).
        for cell in facts.orphan_constant_cells:
            findings.append(
                ReviewFinding(
                    check_id=ReviewCheckId.FAST_LINT,
                    severity=CheckSeverity.BLOCKING,
                    defect_class=DefectClass.MECHANICAL,
                    message=_ORPHAN_MESSAGE,
                    locator=cell,
                )
            )

        # MECHANICAL — inconsistent rows, in the caller-given row order (determinism).
        for row in facts.rows:
            if not row.formula_consistent:
                findings.append(
                    ReviewFinding(
                        check_id=ReviewCheckId.FAST_LINT,
                        severity=CheckSeverity.BLOCKING,
                        defect_class=DefectClass.MECHANICAL,
                        message=_ROW_MESSAGE,
                        locator=row.row_label,
                    )
                )

        # OMISSION — expected line-items missing from the model. A ``frozenset`` has no
        # intrinsic order, so sort the difference for a stable, reproducible sequence.
        missing = sorted(facts.expected_line_items - facts.present_line_items)
        for item in missing:
            findings.append(
                ReviewFinding(
                    check_id=ReviewCheckId.FAST_LINT,
                    severity=CheckSeverity.BLOCKING,
                    defect_class=DefectClass.OMISSION,
                    message=_MISSING_MESSAGE,
                    locator=item,
                )
            )

        return tuple(findings)
