"""Typed content spec for a structured business document.

What this does
--------------
Defines the immutable, validated input contract for
:mod:`autofirm.artifacts.business_document_builder`. A document is a titled
report with an optional executive summary and an ordered sequence of sections,
each with a heading and one or more body paragraphs (Minto answer-first
storyline, ``docs/research/B15-artifact-generation`` §2.3).

Why it exists / where it sits
-----------------------------
Separating the spec from the renderer keeps the document builder general
(CLAUDE.md §3.9) and lets any source — a finance commentary, a board memo, a
test fixture — author a report as structured data, with rendering handled
elsewhere (content/rendering split). Structural validity is enforced here at
construction (fail-closed — CLAUDE.md §5.6).

Security / compliance invariants upheld
---------------------------------------
``__post_init__`` refuses an empty title, an empty section list, an empty
heading, or a section with no body paragraphs with :class:`ArtifactSpecError`, so
a malformed report never reaches the renderer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from autofirm.artifacts.artifact_spec_validation_errors import ArtifactSpecError

__all__ = ["DocumentSection", "DocumentSpec"]


@dataclass(frozen=True, slots=True)
class DocumentSection:
    """One report section: a heading plus its body paragraphs.

    Args:
        heading: Section heading (non-empty).
        paragraphs: Body paragraphs in order; at least one, each non-empty.

    Raises:
        ArtifactSpecError: If the heading is empty, there are no paragraphs, or
            any paragraph is blank (fail-closed — CLAUDE.md §5.6).
    """

    heading: str
    paragraphs: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate the section's heading and body."""
        if not self.heading.strip():  # fail-closed: a section needs a heading
            raise ArtifactSpecError("document section heading must be non-empty")
        if not self.paragraphs:  # fail-closed: an empty section is a content gap
            raise ArtifactSpecError(f"section {self.heading!r} needs at least one paragraph")
        for para in self.paragraphs:
            if not para.strip():  # fail-closed: a blank paragraph is a content gap
                raise ArtifactSpecError(f"section {self.heading!r} has an empty paragraph")


@dataclass(frozen=True, slots=True)
class DocumentSpec:
    """A complete, validated business document.

    Args:
        title: Report title (non-empty).
        sections: Ordered sections; at least one.
        executive_summary: Optional answer-first summary paragraph shown before
            the first section (Minto).

    Raises:
        ArtifactSpecError: If the title is empty or there are no sections
            (fail-closed — CLAUDE.md §5.6).
    """

    title: str
    sections: tuple[DocumentSection, ...]
    executive_summary: str = field(default="")

    def __post_init__(self) -> None:
        """Validate document-level structure."""
        if not self.title.strip():  # fail-closed: an untitled report is refused
            raise ArtifactSpecError("document title must be non-empty")
        if not self.sections:  # fail-closed: a report with no sections is meaningless
            raise ArtifactSpecError("document needs at least one section")
