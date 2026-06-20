"""Teeth-tests for the ReviewableArtifact handle contract.

Prove the handle a check reads from is fail-closed and frozen (CLAUDE.md §5.6):
blank ref refused, unknown kind impossible, immutable so checks cannot mutate shared
state (independence — plan §B.3), and synthetic-only value maps carried by value.
"""

from __future__ import annotations

from decimal import Decimal
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
from autofirm.output_review.reviewable_artifact_facts import (
    NumericClaim,
    NumericClaimSet,
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
        numeric_claims=NumericClaimSet(
            claims=(
                NumericClaim(
                    label="rev_fy24",
                    declared_value=Decimal("100"),
                    recomputed_value=Decimal("100"),
                ),
            )
        )
    )
    assert a.kind is ArtifactKind.FINANCIAL_MODEL
    assert a.numeric_claims is not None
    assert a.numeric_claims.claims[0].label == "rev_fy24"


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
    assert a.balance_sheet is None
    assert a.numeric_claims is None
    assert a.spec_round_trip is None
    assert a.model_lint is None
    assert a.deck_facts is None


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


# ---- EXACT error-message pin (kill the string-literal XX..XX mutant) --------------
# A substring check cannot kill a wrapped string literal; assert the FULL message ==.

_NON_BLANK_REF_MESSAGE = "ReviewableArtifact artifact_ref must be non-blank"


def test_blank_ref_exact_error_text() -> None:
    with pytest.raises(OutputReviewError) as exc:
        _valid(artifact_ref="   ")
    assert str(exc.value) == _NON_BLANK_REF_MESSAGE


# ---- EXACT ArtifactKind value strings (kill the per-member value-literal mutants) -


def test_artifact_kind_member_values_exact() -> None:
    assert ArtifactKind.FINANCIAL_MODEL.value == "FINANCIAL_MODEL"
    assert ArtifactKind.SLIDE_DECK.value == "SLIDE_DECK"
    assert ArtifactKind.BUSINESS_DOCUMENT.value == "BUSINESS_DOCUMENT"


def test_artifact_kind_membership_complete() -> None:
    # Closed set pinned exactly: an added/removed kind FAILS here.
    assert set(ArtifactKind) == {
        ArtifactKind.FINANCIAL_MODEL,
        ArtifactKind.SLIDE_DECK,
        ArtifactKind.BUSINESS_DOCUMENT,
    }
