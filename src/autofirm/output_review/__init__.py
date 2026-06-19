"""The independent human-facing output-review gate for AutoFirm.

What this package does
----------------------
Provides the fail-closed gate that stands between AutoFirm's artifact builders and
any human (owner, CEO, investor): nothing is delivered until an INDEPENDENT,
multi-pass review has verified it is error-free. The gate runs N independent,
deterministic checks over a built artifact and composes a typed
:class:`ReviewVerdict` whose ``passed`` flag is *derived* from the findings — so a
green-but-wrong verdict cannot be manufactured (the false-pass guard).

Why it exists / where it sits
-----------------------------
Per ``docs/research/B16-output-review-and-verification/SYNTHESIS.md`` and the
ratified plan ``docs/architecture/human-output-review-gate-plan.md``: acceptance
NEVER comes from the builder's self-assessment (self-review catches only ~half of
errors), so an independent evaluator grades every artifact against a deterministic
rubric before delivery. This module is the P0 *contract layer* — the typed,
frozen vocabulary (severity / check-id / defect-class / finding / artifact / verdict)
and the check Protocol + registry that the deterministic checks (P1) and the gate
(P2) are built against.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
Fail-closed throughout: blanks and ambiguity resolve to *not passed*; a BLOCKING
finding can never be cleared; duplicate/unknown check registrations are refused;
findings and verdicts carry opaque references only — never raw artifact content
(hashes-not-PII, T1).
"""

from __future__ import annotations

from autofirm.output_review.accounting_identity_check import AccountingIdentityCheck
from autofirm.output_review.fast_lint_check import FastLintCheck
from autofirm.output_review.file_opens_clean_check import (
    FileOpenProbe,
    FileOpensCleanCheck,
)
from autofirm.output_review.ibcs_success_rubric_check import IbcsSuccessRubricCheck
from autofirm.output_review.numeric_recomputation_check import NumericRecomputationCheck
from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.review_check_protocol import CheckRegistry, ReviewCheck
from autofirm.output_review.review_finding_and_severity_contracts import (
    CHECK_DEFECT_CLASSES,
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
    ReviewFinding,
)
from autofirm.output_review.review_verdict_contract import ReviewVerdict
from autofirm.output_review.reviewable_artifact_contract import (
    ArtifactKind,
    ReviewableArtifact,
)
from autofirm.output_review.reviewable_artifact_facts import (
    BalanceSheetFigures,
    BalanceSheetPeriod,
    DeckElementFacts,
    DeckStructuralFacts,
    ModelLintFacts,
    ModelRowFormulaFacts,
    NumericClaim,
    NumericClaimSet,
    SpecRoundTrip,
)
from autofirm.output_review.spec_artifact_round_trip_check import SpecRoundTripCheck
from autofirm.output_review.visual_integrity_lint_check import VisualIntegrityLintCheck

__all__ = [
    "CHECK_DEFECT_CLASSES",
    "AccountingIdentityCheck",
    "ArtifactKind",
    "BalanceSheetFigures",
    "BalanceSheetPeriod",
    "CheckRegistry",
    "CheckSeverity",
    "DeckElementFacts",
    "DeckStructuralFacts",
    "DefectClass",
    "FastLintCheck",
    "FileOpenProbe",
    "FileOpensCleanCheck",
    "IbcsSuccessRubricCheck",
    "ModelLintFacts",
    "ModelRowFormulaFacts",
    "NumericClaim",
    "NumericClaimSet",
    "NumericRecomputationCheck",
    "OutputReviewError",
    "ReviewCheck",
    "ReviewCheckId",
    "ReviewFinding",
    "ReviewVerdict",
    "ReviewableArtifact",
    "SpecRoundTrip",
    "SpecRoundTripCheck",
    "VisualIntegrityLintCheck",
]
