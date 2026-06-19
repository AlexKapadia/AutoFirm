"""Teeth-tests for the ReviewableArtifact handle contract.

Prove the handle a check reads from is fail-closed and frozen (CLAUDE.md §5.6):
blank ref refused, unknown kind impossible, immutable so checks cannot mutate shared
state (independence — plan §B.3), and synthetic-only value maps carried by value.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.reviewable_artifact_contract import (
    ArtifactKind,
    ReviewableArtifact,
)


def _valid(**over: object) -> ReviewableArtifact:
    base: dict[str, object] = {
        "artifact_ref": "sha256:abc",
        "kind": ArtifactKind.FINANCIAL_MODEL,
        "path": Path("/synthetic/model.xlsx"),
    }
    base.update(over)
    return ReviewableArtifact(**base)  # type: ignore[arg-type]


def test_valid_artifact_constructs() -> None:
    a = _valid(
        recomputed_values={"rev_fy24": "100"}, declared_values={"rev_fy24": "100"}
    )
    assert a.kind is ArtifactKind.FINANCIAL_MODEL
    assert a.recomputed_values == {"rev_fy24": "100"}


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_ref_refused(blank: str) -> None:
    with pytest.raises(OutputReviewError):
        _valid(artifact_ref=blank)


def test_unknown_kind_refused() -> None:
    with pytest.raises(ValidationError):
        _valid(kind="HOLOGRAM")  # not an ArtifactKind member


def test_artifact_is_frozen() -> None:
    a = _valid()
    with pytest.raises(ValidationError):
        a.artifact_ref = "tampered"


def test_extra_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        _valid(bogus=1)


def test_optional_fields_default_none() -> None:
    a = _valid()
    assert a.originating_spec is None
    assert a.recomputed_values is None
    assert a.declared_values is None


def test_arbitrary_spec_object_accepted_opaquely() -> None:
    # The originating spec is opaque to the contract layer (another lane's type).
    spec = object()
    a = _valid(originating_spec=spec)
    assert a.originating_spec is spec


def test_path_is_typed_path() -> None:
    a = _valid(path=Path("rel/deck.pptx"))
    assert isinstance(a.path, Path)


@settings(max_examples=200)
@given(
    ref=st.text(min_size=1, max_size=40).filter(str.strip),
    kind=st.sampled_from(list(ArtifactKind)),
)
def test_property_any_nonblank_ref_and_valid_kind_constructs(
    ref: str, kind: ArtifactKind
) -> None:
    a = ReviewableArtifact(artifact_ref=ref, kind=kind, path=Path("/x"))
    assert a.artifact_ref == ref and a.kind is kind


@settings(max_examples=150)
@given(ref=st.text(max_size=5).filter(lambda s: not s.strip()))
def test_property_any_blank_ref_refused(ref: str) -> None:
    with pytest.raises(OutputReviewError):
        ReviewableArtifact(artifact_ref=ref, kind=ArtifactKind.SLIDE_DECK, path=Path("/x"))
