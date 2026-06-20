"""The delivery admission guard: nothing is filed without an authorised release.

What this does
--------------
Provides :func:`require_authorised_release`, the single fail-closed assertion that
every outbound artifact-delivery seam calls BEFORE it mutates any store/catalog.
It refuses delivery unless the caller holds a genuine, authorised
:class:`~autofirm.output_review.release_decision_gate.ReleaseDecision` whose
``artifact_ref`` binds to the exact artifact being delivered.

Why it exists / where it sits
-----------------------------
The output-review lane re-derives pass/fail into a :class:`ReleaseDecision`
(``authorised`` is derived from ``final_verdict.passed`` — a false pass is
unconstructible). But a *decision object* only protects delivery if the delivery
seam actually CHECKS it. This guard is that check: it turns the release authority
into a load-bearing precondition at the artifact-delivery chokepoint (the
librarian's ``file``), so an un-reviewed or wrongly-authorised artifact can never
be filed. It depends only on the P2 contract + the lane's error type, so any
delivery seam can import it without pulling in the gate machinery.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Fail closed on a missing decision:** a ``None`` decision (no review ran, or the
  caller forgot to gate) is refused — absence of proof is never proof.
* **Fail closed on an unauthorised release:** ``decision.authorised`` must be truthy;
  a failing verdict (``authorised`` False) — or the structurally-impossible ``None``
  — is refused, so a blocked artifact cannot be smuggled through.
* **Ref binding (anti-swap):** when ``expected_artifact_ref`` is supplied, the
  decision's ``artifact_ref`` must equal it — this stops ONE authorised release from
  being reused to deliver a DIFFERENT artifact (the ref-swap hole).
"""

from __future__ import annotations

from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.release_decision_gate import ReleaseDecision

__all__ = ["require_authorised_release"]


def require_authorised_release(
    decision: ReleaseDecision | None,
    *,
    expected_artifact_ref: str | None = None,
) -> None:
    """Refuse delivery unless ``decision`` is an authorised, ref-matching release.

    Call this as the FIRST statement of any outbound delivery seam, before any
    store or catalog mutation, so a refusal happens *before* side effects.

    Args:
        decision: The release authority's verdict for THIS delivery, or ``None``
            when the caller obtained no decision at all (an un-gated path).
        expected_artifact_ref: If supplied, the stable identity of the artifact
            actually being delivered. The decision must authorise *that* artifact
            (``decision.artifact_ref == expected_artifact_ref``); a mismatch is the
            ref-swap attack and is refused. ``None`` skips the binding check (the
            seam is asserting authorisation only).

    Raises:
        OutputReviewError: if ``decision`` is ``None`` (no proof of review), if it
            is not authorised (the verdict did not pass), or if a supplied
            ``expected_artifact_ref`` does not match the decision's ``artifact_ref``
            (a decision for a different artifact). Every refusal is fail-closed —
            delivery is blocked, never allowed to proceed (CLAUDE.md §5.6).
    """
    if decision is None:
        # fail-closed: no decision means no review proof — refuse delivery outright.
        raise OutputReviewError(
            "delivery refused: no ReleaseDecision supplied — an authorised release "
            "is required before filing"
        )
    if not decision.authorised:
        # fail-closed: a non-authorised (or impossible None) release means the verdict
        # did NOT pass — the artifact is blocked and must not be delivered.
        raise OutputReviewError(
            "delivery refused: ReleaseDecision is not authorised — the review "
            "verdict did not pass"
        )
    if expected_artifact_ref is not None and decision.artifact_ref != expected_artifact_ref:
        # fail-closed (anti-swap): this authorised release is for a DIFFERENT
        # artifact than the one being filed — refuse so one valid release cannot be
        # replayed to smuggle an unrelated artifact through the seam.
        raise OutputReviewError(
            "delivery refused: ReleaseDecision authorises "
            f"{decision.artifact_ref!r}, not the artifact being filed "
            f"{expected_artifact_ref!r}"
        )
