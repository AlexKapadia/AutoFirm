"""The ACCOUNTING_IDENTITY deterministic check: A = L + E, exact to the unit.

What this does
--------------
Implements :class:`AccountingIdentityCheck`, the deterministic-floor check that
verifies the fundamental accounting identity ``assets == liabilities + equity`` for
every period of a financial model's balance sheet. It satisfies the
:class:`~autofirm.output_review.review_check_protocol.ReviewCheck` Protocol: it
exposes the :class:`~autofirm.output_review.review_finding_and_severity_contracts.ReviewCheckId`
it owns and a pure, deterministic ``run`` that returns the
:class:`~autofirm.output_review.review_finding_and_severity_contracts.ReviewFinding`
tuple it raises (empty == clean).

The comparison is **exact** — a raw :class:`~decimal.Decimal` equality, never a
tolerance. A balance sheet off by ``Decimal("0.01")`` is a defect, because a
financial statement that does not balance to the unit is wrong (CLAUDE.md §3.11
zero-numerical-error). Pure-logic class: the identity has the right *structure*
(three figures per period) but a wrong *value* relationship — exactly the
Panko-Halverson PURE_LOGIC bucket this check is registered under.

Why it exists / where it sits
-----------------------------
``SYNTHESIS.md`` §2.2/§3 makes the deterministic floor a set of independent, pure
checks; this is the ACCOUNTING_IDENTITY member. It reads only the by-value
``balance_sheet`` fact bundle the caller populated on the
:class:`~autofirm.output_review.reviewable_artifact_contract.ReviewableArtifact`,
so it is a pure function of plain data with no IO, clock, or randomness — verdicts
built from it are reproducible (Protocol determinism contract).

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Fail closed on missing facts:** if a FINANCIAL_MODEL carries no
  ``balance_sheet`` bundle, the check cannot verify the identity, so it emits ONE
  BLOCKING finding rather than vacuously passing — an unverifiable model is refused,
  never waved through.
* **Exact, not tolerant:** the identity is checked with raw ``Decimal`` equality;
  no epsilon, no rounding, no "close enough" — a sub-unit imbalance still blocks.
* **Pure & deterministic:** ``run`` reads only the frozen artifact, performs no IO,
  consults no clock/RNG, and mutates nothing — the same artifact always yields the
  same ordered findings tuple (period order as given).
* **Defect-class consistency:** every finding is classified ``PURE_LOGIC``, which is
  a member of ``CHECK_DEFECT_CLASSES[ACCOUNTING_IDENTITY]`` — the finding can never
  carry a class this check does not own.
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
    from autofirm.output_review.reviewable_artifact_facts import BalanceSheetPeriod

__all__ = ["AccountingIdentityCheck"]

# The single defect class this check raises. PURE_LOGIC because a balance sheet that
# does not satisfy A = L + E has the right structure but a wrong value relationship
# (Panko-Halverson). Asserted against CHECK_DEFECT_CLASSES in the teeth-tests so the
# constant can never drift out of the check's registered class set.
_DEFECT_CLASS = DefectClass.PURE_LOGIC

# Message used when a financial model arrives with no balance-sheet facts to check.
# Fail-closed (CLAUDE.md §5.6): we cannot verify the identity, so we refuse rather
# than pass — the absence itself is the blocking defect.
_ABSENT_FACTS_MESSAGE = "balance-sheet facts absent — cannot verify A=L+E"


class AccountingIdentityCheck:
    """Verify ``assets == liabilities + equity`` per period, exact to the unit.

    Implements the :class:`~autofirm.output_review.review_check_protocol.ReviewCheck`
    Protocol for :attr:`ReviewCheckId.ACCOUNTING_IDENTITY`. The check is stateless;
    a single instance may be reused across artifacts because ``run`` holds no state.

    Inputs
    ------
    ``run`` takes one
    :class:`~autofirm.output_review.reviewable_artifact_contract.ReviewableArtifact`
    and reads only its ``kind`` and (by value) ``balance_sheet`` facts.

    Outputs
    -------
    An ordered ``tuple[ReviewFinding, ...]`` (empty == clean):

    * ``kind`` is not :attr:`ArtifactKind.FINANCIAL_MODEL` -> ``()`` (not applicable).
    * ``kind`` is a financial model but ``balance_sheet`` is ``None`` -> exactly one
      BLOCKING finding (the identity cannot be verified — fail-closed).
    * otherwise -> one BLOCKING finding per imbalanced period, in the period order
      given; ``()`` when every period balances.

    Failure modes
    -------------
    ``run`` raises nothing of its own: malformed facts are refused upstream at
    contract-construction time (e.g. ``float`` figures, empty/duplicate periods).
    It is pure and deterministic — no IO, no clock, no randomness, no mutation — so
    the same artifact always yields the byte-identical findings tuple.
    """

    @property
    def id(self) -> ReviewCheckId:
        """The closed-set id this check owns (its registry key)."""
        return ReviewCheckId.ACCOUNTING_IDENTITY

    def run(self, artifact: ReviewableArtifact) -> tuple[ReviewFinding, ...]:
        """Return the imbalance findings for ``artifact`` (empty tuple == clean).

        See the class docstring for the full applicability ladder. The method is a
        pure function of ``artifact``: it branches on ``kind``, refuses fail-closed
        when a financial model lacks balance-sheet facts, and otherwise compares each
        period with exact :class:`~decimal.Decimal` equality.
        """
        # Applicability gate: the accounting identity is meaningful only for a
        # spreadsheet financial model. Any other kind is simply not this check's job,
        # so it declines with an empty tuple (not a defect — just inapplicable).
        if artifact.kind is not ArtifactKind.FINANCIAL_MODEL:
            return ()

        # fail-closed: a financial model with no balance-sheet facts cannot be
        # verified — emit one BLOCKING finding rather than vacuously pass (§5.6).
        if artifact.balance_sheet is None:
            return (self._absent_facts_finding(artifact.artifact_ref),)

        # One BLOCKING finding per period whose figures do not satisfy A = L + E,
        # in the period order given (deterministic). A period that balances yields
        # nothing; an all-balanced sheet yields the empty tuple.
        findings = tuple(
            self._imbalance_finding(period)
            for period in artifact.balance_sheet.periods
            # exact comparison — a sub-unit imbalance (e.g. 0.01) is still a defect.
            if period.assets != period.liabilities + period.equity
        )
        return findings

    @staticmethod
    def _absent_facts_finding(artifact_ref: str) -> ReviewFinding:
        """Build the BLOCKING finding for a model that carries no balance sheet.

        The locator is the artifact reference itself: there is no period to point at,
        so the whole artifact is the defect site. Fail-closed (CLAUDE.md §5.6).
        """
        return ReviewFinding(
            check_id=ReviewCheckId.ACCOUNTING_IDENTITY,
            severity=CheckSeverity.BLOCKING,
            defect_class=_DEFECT_CLASS,
            message=_ABSENT_FACTS_MESSAGE,
            locator=artifact_ref,
        )

    @staticmethod
    def _imbalance_finding(period: BalanceSheetPeriod) -> ReviewFinding:
        """Build the BLOCKING finding for one imbalanced period.

        ``expected``/``actual`` carry the exact two sides of the identity (the raw
        :class:`~decimal.Decimal` values) so a send-back is machine-actionable and
        the verdict explains itself (§3.11). The ``locator`` is the period label so a
        fix targets that exact period, not the whole model.
        """
        lhs_plus = period.liabilities + period.equity
        return ReviewFinding(
            check_id=ReviewCheckId.ACCOUNTING_IDENTITY,
            severity=CheckSeverity.BLOCKING,
            defect_class=_DEFECT_CLASS,
            message=(
                f"accounting identity violated for period {period.period!r}: "
                f"assets != liabilities + equity (exact)"
            ),
            locator=period.period,
            expected=f"A={period.assets}",
            actual=f"L+E={lhs_plus}",
        )
