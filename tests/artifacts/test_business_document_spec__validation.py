"""Adversarial validation tests for the business-document spec contract.

Proves the document spec is fail-closed (CLAUDE.md §5.6): empty titles, empty
section lists, headingless or bodyless sections, and blank paragraphs are all
refused at construction before the renderer runs.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.artifacts.artifact_spec_validation_errors import ArtifactSpecError
from autofirm.artifacts.business_document_spec import DocumentSection, DocumentSpec


def test_valid_document_constructs() -> None:
    spec = DocumentSpec(title="Report", sections=(DocumentSection("Intro", ("Body.",)),))
    assert spec.sections[0].heading == "Intro"


@pytest.mark.parametrize("title", ["", "   ", "\n"])
def test_blank_title_refused(title: str) -> None:
    with pytest.raises(ArtifactSpecError, match="title"):
        DocumentSpec(title=title, sections=(DocumentSection("H", ("p",)),))


def test_no_sections_refused() -> None:
    with pytest.raises(ArtifactSpecError, match="at least one section"):
        DocumentSpec(title="Report", sections=())


@pytest.mark.parametrize("heading", ["", "  "])
def test_blank_section_heading_refused(heading: str) -> None:
    with pytest.raises(ArtifactSpecError, match="heading"):
        DocumentSection(heading, ("p",))


def test_section_with_no_paragraphs_refused() -> None:
    with pytest.raises(ArtifactSpecError, match="at least one paragraph"):
        DocumentSection("Heading", ())


@pytest.mark.parametrize("paragraphs", [("",), ("ok", "   "), ("\t",)])
def test_blank_paragraph_refused(paragraphs: tuple[str, ...]) -> None:
    with pytest.raises(ArtifactSpecError, match="empty paragraph"):
        DocumentSection("Heading", paragraphs)


@pytest.mark.property
@given(
    n_sections=st.integers(min_value=1, max_value=5),
    n_paras=st.integers(min_value=1, max_value=4),
)
def test_arbitrary_well_formed_document_constructs(n_sections: int, n_paras: int) -> None:
    sections = tuple(
        DocumentSection(f"Section {s}", tuple(f"Para {s}.{p}" for p in range(n_paras)))
        for s in range(n_sections)
    )
    spec = DocumentSpec(title="Generated", sections=sections)
    assert len(spec.sections) == n_sections
