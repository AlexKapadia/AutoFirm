"""The handle a review check operates on: file + originating spec + recomputed values.

What this does
--------------
Defines :class:`ArtifactKind` (the closed set of deliverable kinds the gate reviews)
and :class:`ReviewableArtifact` — the frozen handle every :class:`ReviewCheck` reads
from. It carries:

* ``kind`` — what the artifact is (spreadsheet model / slide deck / document), so a
  check can decline kinds it does not apply to.
* ``path`` — where the built file lives on disk (the bytes the structural checks read).
* ``originating_spec`` — the builder spec the artifact was generated from, so a
  spec<->artifact round-trip check can prove every declared value is present & correct.
* ``recomputed_values`` / ``declared_values`` — the value maps the deterministic
  numeric checks compare exactly (recomputed formula results vs the file's cached
  values; declared spec figures vs what was written) — CLAUDE.md §3.11.

Why it exists / where it sits
-----------------------------
``SYNTHESIS.md`` §2.2 makes the deterministic floor a *pure function of (file bytes
+ spec)*. This contract is exactly that input bundle, passed by value (frozen) so a
check cannot mutate the artifact under another check (independence — plan §B.3). It
sits upstream of every check and the gate that composes them.

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.12)
--------------------------------------------------------------
* **No real PII — synthetic/opaque only:** the value maps hold opaque, synthetic,
  string-keyed scalars (the recomputed/declared figures the checks compare), never
  real client data or document bytes. Real artifact content stays on disk behind
  ``path``; this handle never inlines it.
* **Fail closed on blanks / missing file context:** a blank ``artifact_ref`` is
  refused at construction; ``path`` is a real ``Path`` (type-checked), so a check
  that needs the file cannot be handed an empty reference.
* **Frozen & immutable:** checks receive the same handle and cannot mutate shared
  state, so the gate's composition of independent checks stays deterministic.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.output_review.output_review_errors import OutputReviewError

__all__ = [
    "ArtifactKind",
    "ReviewableArtifact",
]


class ArtifactKind(StrEnum):
    """The closed set of deliverable kinds the gate reviews.

    A check inspects ``kind`` to decide whether it applies (e.g. ACCOUNTING_IDENTITY
    applies to a financial model, not a slide deck). A fixed enumeration so a check
    can never be handed an unclassifiable artifact.
    """

    FINANCIAL_MODEL = "FINANCIAL_MODEL"  # spreadsheet model (xlsx)
    SLIDE_DECK = "SLIDE_DECK"  # presentation deck (pptx)
    BUSINESS_DOCUMENT = "BUSINESS_DOCUMENT"  # narrative document (docx/pdf)


class ReviewableArtifact(BaseModel):
    """A frozen, by-value handle a deterministic check reads from.

    Inputs
    ------
    * ``artifact_ref`` — opaque, stable reference to the artifact (e.g. a content
      hash or store key) used in verdicts and audit records — never raw content.
    * ``kind`` — the :class:`ArtifactKind`.
    * ``path`` — on-disk location of the built file the structural checks read.
    * ``originating_spec`` — the builder spec; opaque to the contract layer (the
      round-trip check knows its concrete shape). Optional for kinds without a spec.
    * ``recomputed_values`` — recomputed formula results, by opaque key (synthetic).
    * ``declared_values`` — values the spec declared / the file cached, by opaque key.

    Failure modes
    -------------
    Raises :class:`OutputReviewError` on a blank ``artifact_ref`` (an unidentifiable
    artifact cannot be audited — fail-closed, CLAUDE.md §5.6).
    """

    # arbitrary_types_allowed: ``originating_spec`` is an opaque builder spec object
    # whose concrete type lives in another lane; the contract layer never inspects it.
    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    artifact_ref: str
    kind: ArtifactKind
    path: Path
    originating_spec: object | None = None
    recomputed_values: Mapping[str, object] | None = None
    declared_values: Mapping[str, object] | None = None

    @field_validator("artifact_ref")
    @classmethod
    def _non_blank_ref(cls, value: str) -> str:
        # fail-closed: an unidentifiable artifact cannot be referenced in a verdict
        # or audit record — refuse it rather than review something we cannot name.
        if not value or not value.strip():
            raise OutputReviewError("ReviewableArtifact artifact_ref must be non-blank")
        return value
