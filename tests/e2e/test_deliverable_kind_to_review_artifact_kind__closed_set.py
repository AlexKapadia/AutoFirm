"""Teeth-tests for the DeliverableKind -> ArtifactKind mapper (fail-closed).

Proves every reviewable store kind maps to the right review family, and that the
un-reviewable IMAGE kind and any out-of-vocabulary value are REFUSED — a wrong or
silent mapping would gate a deliverable under the wrong checks (a false pass).
"""

from __future__ import annotations

import pytest

from autofirm.document_store.filed_document_record import DeliverableKind
from autofirm.e2e.deliverable_kind_to_review_artifact_kind import review_artifact_kind_for
from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.reviewable_artifact_contract import ArtifactKind


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        (DeliverableKind.REPORT, ArtifactKind.BUSINESS_DOCUMENT),
        (DeliverableKind.DOC, ArtifactKind.BUSINESS_DOCUMENT),
        (DeliverableKind.MODEL, ArtifactKind.FINANCIAL_MODEL),
        (DeliverableKind.DECK, ArtifactKind.SLIDE_DECK),
    ],
)
def test_reviewable_kinds_map_to_their_family(
    kind: DeliverableKind, expected: ArtifactKind
) -> None:
    assert review_artifact_kind_for(kind) is expected


def test_image_kind_is_refused() -> None:
    # IMAGE has no OOXML/PDF review family — it must NOT be mapped to a document.
    with pytest.raises(OutputReviewError) as exc:
        review_artifact_kind_for(DeliverableKind.IMAGE)
    assert str(exc.value) == "deliverable kind 'image' has no reviewable artifact kind"


def test_unknown_value_is_refused() -> None:
    # A value outside the closed DeliverableKind vocabulary falls to the wildcard
    # and is refused (defends a future enum member added without a mapping).
    with pytest.raises(OutputReviewError) as exc:
        review_artifact_kind_for("totally-unknown")  # type: ignore[arg-type]
    assert str(exc.value) == "unknown deliverable kind 'totally-unknown'"


def test_every_enum_member_is_handled() -> None:
    # No DeliverableKind silently falls through: each member either maps or raises
    # the IMAGE refusal — never returns None / an unexpected family.
    for kind in DeliverableKind:
        if kind is DeliverableKind.IMAGE:
            with pytest.raises(OutputReviewError):
                review_artifact_kind_for(kind)
        else:
            assert isinstance(review_artifact_kind_for(kind), ArtifactKind)
