"""Builds the targeted send-back from a FAILED verdict — never from a clean one.

What this does
--------------
Defines :func:`build_correction_send_back`, the single function that turns a *failed*
:class:`ReviewVerdict` into a :class:`CorrectionSendBack`. It extracts the verdict's
BLOCKING findings (via the verdict's own ``blocking_findings`` property) and packages
them with the artifact reference and attempt number, so the builder that regenerates
the artifact is told *exactly* which defect sites to fix.

Why it exists / where it sits
-----------------------------
Per ``docs/research/B16-output-review-and-verification/SYNTHESIS.md`` (the
generator/evaluator send-back loop): a re-review cycle is only useful if the
send-back is *actionable*. This function is the bridge between the verdict contract
(P0) and the bounded correction loop (:mod:`correction_loop_state`) — it guarantees
that only the blocking subset travels back, so regeneration is targeted, not blind.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Never send back a passing artifact:** if ``verdict.passed`` is True there is no
  blocking defect, so the function refuses fail-closed (:class:`OutputReviewError`)
  rather than fabricating an empty/pointless send-back.
* **Blocking-only payload:** advisory findings are excluded — they never justify a
  regeneration — so the builder is not chased over non-blocking notes.
* **Self-explaining:** the carried findings keep their locator / expected / actual,
  so every send-back explains precisely what must change (explain-every-decision).
"""

from __future__ import annotations

from autofirm.output_review.correction_loop_state import CorrectionSendBack
from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.review_verdict_contract import ReviewVerdict

__all__ = ["build_correction_send_back"]


def build_correction_send_back(
    verdict: ReviewVerdict, attempt: int
) -> CorrectionSendBack:
    """Package a FAILED verdict's BLOCKING findings into a targeted send-back.

    Inputs
    ------
    * ``verdict`` — the review pass to send back; MUST be a failing verdict (i.e.
      ``verdict.passed is False``, equivalently at least one BLOCKING finding).
    * ``attempt`` — the 1-based attempt number this send-back belongs to.

    Returns a :class:`CorrectionSendBack` carrying the verdict's ``artifact_ref``,
    its BLOCKING findings ONLY (advisory findings excluded), and ``attempt``.

    Failure modes
    -------------
    Raises :class:`OutputReviewError` if ``verdict.passed`` is True — you never send
    back a clean artifact (fail-closed, CLAUDE.md §5.6). The downstream
    :class:`CorrectionSendBack` construction additionally refuses a non-positive
    ``attempt`` or any non-blocking finding, so a malformed send-back is impossible.
    """
    if verdict.passed:
        # fail-closed: a passing verdict has no blocking defect to correct, so a
        # send-back would be meaningless — refuse rather than emit an empty one.
        raise OutputReviewError(
            "build_correction_send_back: cannot send back a PASSING verdict "
            f"(artifact_ref={verdict.artifact_ref!r}) — nothing to correct"
        )
    # blocking_findings is the verdict's own derived blocking subset (advisory
    # findings dropped here), so the regeneration targets exactly the failure sites.
    return CorrectionSendBack(
        artifact_ref=verdict.artifact_ref,
        blocking_findings=verdict.blocking_findings,
        attempt=attempt,
    )
