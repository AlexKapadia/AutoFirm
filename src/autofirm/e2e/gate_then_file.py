"""The review-then-file seam: nothing is catalogued without an authorised release.

What this does
--------------
Provides :func:`gate_then_file`, the single helper every e2e delivery call site
uses to route a built artifact through the output-review lane BEFORE it is filed:

1. assert the reviewable artifact's ref binds to the record being filed,
2. REVIEW the artifact through the output-review gate (a derived verdict),
3. DECIDE a release on that verdict through the release gate (authorise iff it
   passed, and audit the decision), then
4. FILE the record with that decision — which the librarian's admission guard
   re-checks, so a non-authorised or ref-mismatched decision is refused before any
   catalog mutation.

Why it exists / where it sits
-----------------------------
The librarian's ``file`` already REQUIRES an authorised, ref-bound
:class:`~autofirm.output_review.release_decision_gate.ReleaseDecision`. This helper
is how a call site *obtains* that decision honestly — by actually reviewing the
real file — so the two e2e delivery paths share one correct, fail-closed sequence
instead of each re-implementing (and risking faking) the gate→decide→file dance.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Ref binding at the source:** the artifact under review MUST carry the same
  ``artifact_ref`` the record will be filed under (``release_artifact_ref_for``);
  a mismatch is refused here, before any review, so a decision can never be made
  for one artifact and used to file another (anti-swap, defence-in-depth with the
  librarian's own guard).
* **Fail closed for free:** a failing review yields an un-authorised decision, and
  ``librarian.file`` then refuses the filing via the admission guard — so a blocked
  artifact is NEVER catalogued, with no special-casing in this helper.
* **Real review of a real file:** the verdict comes from running the gate over the
  artifact handle (whose FILE_OPENS_CLEAN probe reads the bytes and whose
  SPEC_ROUND_TRIP facts were re-read from disk) — never a synthesised pass.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autofirm.document_store.librarian_filing_service import release_artifact_ref_for
from autofirm.output_review.output_review_errors import OutputReviewError

if TYPE_CHECKING:
    from autofirm.document_store.filed_document_record import FiledDocumentRecord
    from autofirm.document_store.librarian_filing_service import (
        CatalogEntry,
        LibrarianFilingService,
    )
    from autofirm.output_review.output_review_gate import OutputReviewGate
    from autofirm.output_review.release_decision_gate import ReleaseDecisionGate
    from autofirm.output_review.reviewable_artifact_contract import ReviewableArtifact

__all__ = ["gate_then_file"]


def gate_then_file(  # noqa: PLR0913 -- record + artifact + review gate + release gate are all explicit collaborators of this seam
    librarian: LibrarianFilingService,
    record: FiledDocumentRecord,
    *,
    artifact: ReviewableArtifact,
    gate: OutputReviewGate,
    release_gate: ReleaseDecisionGate,
    reason: str,
) -> CatalogEntry:
    """Review ``artifact``, decide a release, then file ``record`` under it.

    Args:
        librarian: The document store the record is filed into.
        record: The deliverable record to file once a release is authorised.
        artifact: The reviewable handle to the built file; its ``artifact_ref`` MUST
            equal ``release_artifact_ref_for(record)``.
        gate: The output-review gate that produces the verdict over ``artifact``.
        release_gate: The release authority that turns the verdict into an audited,
            ref-bound :class:`ReleaseDecision`.
        reason: Human-readable justification recorded with the release decision.

    Returns:
        The :class:`CatalogEntry` the librarian appended once the filing was
        admitted.

    Raises:
        OutputReviewError: if the artifact's ref does not bind to ``record``
            (refused before review), or — via the librarian's admission guard — if
            the review verdict did not pass (a blocked artifact is never filed).
    """
    expected_ref = release_artifact_ref_for(record)
    if artifact.artifact_ref != expected_ref:
        # fail-closed: review the EXACT artifact being filed, never a stand-in — a
        # ref mismatch here would let a passing review for X authorise filing Y.
        raise OutputReviewError(
            "gate_then_file: artifact ref "
            f"{artifact.artifact_ref!r} does not bind to record ref {expected_ref!r}"
        )

    verdict = gate.review(artifact)  # real review of the real file (derived passed)
    decision = release_gate.decide(verdict, reason)  # authorise iff passed; audited
    # The librarian re-checks the decision (authorised + ref-bound) BEFORE any
    # catalog mutation, so a denied release raises here and nothing is filed.
    return librarian.file(record, release_decision=decision)
