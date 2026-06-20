"""Map a store DeliverableKind to the review lane's ArtifactKind, fail-closed.

What this does
--------------
Provides :func:`review_artifact_kind_for`, the closed-set pure function that
translates a :class:`~autofirm.document_store.filed_document_record.DeliverableKind`
(what the document store files) into the
:class:`~autofirm.output_review.reviewable_artifact_contract.ArtifactKind` the
output-review gate reviews. It is the single place that knows which deliverable
kind is reviewed as which artifact kind, so the e2e seam never hard-codes that
mapping at a call site.

Why it exists / where it sits
-----------------------------
The two lanes speak different closed vocabularies: the store enumerates
``REPORT / MODEL / DECK / DOC / IMAGE`` (foldering buckets), while the review gate
enumerates ``BUSINESS_DOCUMENT / FINANCIAL_MODEL / SLIDE_DECK`` (review families).
A deliverable can only be gated once its kind is expressed in the review
vocabulary, so this mapper is the adapter between them.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Fail closed on an un-reviewable kind:** ``IMAGE`` has NO reviewable artifact
  family (the deterministic floor reviews OOXML/PDF deliverables, not raster
  images), so it is REFUSED rather than mapped to a plausible-but-wrong family —
  delivering an un-reviewed image through a document gate would be a false pass.
* **Fail closed on an unknown kind:** a ``DeliverableKind`` not handled above (e.g.
  a future enum member added without a mapping) raises rather than silently
  defaulting, so a new kind cannot slip through the seam unreviewed.
"""

from __future__ import annotations

from autofirm.document_store.filed_document_record import DeliverableKind
from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.reviewable_artifact_contract import ArtifactKind

__all__ = ["review_artifact_kind_for"]

# The closed mapping from a reviewable store kind to its output-review family.
# Narrative deliverables (reports, memos, charters) are reviewed as business
# documents; models and decks map to their own families. IMAGE is deliberately
# ABSENT — it has no OOXML/PDF review family (handled fail-closed below).
_REVIEW_ARTIFACT_KIND: dict[DeliverableKind, ArtifactKind] = {
    DeliverableKind.REPORT: ArtifactKind.BUSINESS_DOCUMENT,
    DeliverableKind.DOC: ArtifactKind.BUSINESS_DOCUMENT,
    DeliverableKind.MODEL: ArtifactKind.FINANCIAL_MODEL,
    DeliverableKind.DECK: ArtifactKind.SLIDE_DECK,
}


def review_artifact_kind_for(kind: DeliverableKind) -> ArtifactKind:
    """Return the review :class:`ArtifactKind` a ``DeliverableKind`` is gated as.

    Args:
        kind: The store deliverable kind to translate.

    Returns:
        The output-review artifact family for ``kind``:
        ``REPORT``/``DOC`` -> ``BUSINESS_DOCUMENT``, ``MODEL`` -> ``FINANCIAL_MODEL``,
        ``DECK`` -> ``SLIDE_DECK``.

    Raises:
        OutputReviewError: if ``kind`` has no reviewable artifact family (``IMAGE``)
            or is an unhandled/unknown kind (fail-closed — CLAUDE.md §5.6).
    """
    mapped = _REVIEW_ARTIFACT_KIND.get(kind)
    if mapped is not None:
        return mapped
    if kind is DeliverableKind.IMAGE:
        # fail-closed: an image has no OOXML/PDF review family; mapping it to a
        # document family would gate it under the wrong checks (a false pass).
        raise OutputReviewError(
            f"deliverable kind {kind.value!r} has no reviewable artifact kind"
        )
    # fail-closed: an unhandled (e.g. newly-added or out-of-vocabulary) kind must
    # not silently map — refuse so a new kind cannot slip through unreviewed.
    raise OutputReviewError(f"unknown deliverable kind {kind!r}")
