"""Build a GENUINE SpecRoundTrip by re-reading a docx title from disk bytes.

What this does
--------------
Provides :func:`build_document_spec_round_trip`, which constructs the
:class:`~autofirm.output_review.reviewable_artifact_facts.SpecRoundTrip` fact the
SPEC_ROUND_TRIP check consumes for a business document. It does so HONESTLY: the
``declared`` value is the title the spec asked for, and the ``extracted`` value is
the title *re-read back out of the written ``.docx``* via :func:`extract_document_title`
— never copied from the spec. If the renderer dropped or mangled the title, the two
values differ and the check blocks; only a real, intact round-trip passes.

Why stdlib, not python-docx
---------------------------
A ``.docx`` is a ZIP whose ``word/document.xml`` is WordprocessingML. The title is
written as the first paragraph in the ``Title`` style, so its text can be re-read
with the standard-library :mod:`zipfile` + :mod:`xml.etree.ElementTree` alone — no
python-docx import, keeping the e2e closure free of OOXML libs (import-linter
contract ``core-runtime-must-not-import-artifact-libs``).

Security / compliance invariants upheld (CLAUDE.md §5.6, §3.11)
--------------------------------------------------------------
* **Genuine round-trip, never tautological:** ``extracted`` comes from the file's
  bytes; it is NEVER set equal to ``declared`` from one source. A vacuous pass is
  impossible by construction.
* **Fail closed on an unreadable / titleless file:** if the docx cannot be opened
  or carries no ``Title`` paragraph, :func:`extract_document_title` raises, so a
  round-trip can never be fabricated over a broken artifact.
* **Deterministic:** parsing the same bytes always yields the same title (no clock,
  no randomness), so the resulting verdict is reproducible.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET  # nosec B405 - parses only trusted, self-produced OOXML
import zipfile
from pathlib import Path

from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.reviewable_artifact_facts import SpecRoundTrip

__all__ = ["TITLE_KEY", "build_document_spec_round_trip", "extract_document_title"]

# The WordprocessingML main namespace every docx body element is qualified with.
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
# The part inside the .docx ZIP that holds the document body.
_DOCUMENT_PART = "word/document.xml"
# The paragraph style python-docx writes the report title under (the renderer's
# ``_write_title`` uses style="Title"); we re-find the title by this style so the
# extraction targets the title specifically, not just "the first text on the page".
_TITLE_STYLE = "Title"
# The single round-trip key checked: the document title declared vs re-read.
TITLE_KEY = "title"


def extract_document_title(docx_path: Path) -> str:
    """Re-read the ``Title``-styled paragraph's text from a written ``.docx``.

    Opens ``docx_path`` as a ZIP, parses ``word/document.xml``, finds the first
    paragraph whose style is ``Title``, and returns the concatenation of its text
    runs — exactly the title string a reader sees, recovered from the file bytes.

    Args:
        docx_path: Path to the written ``.docx`` artifact.

    Returns:
        The document title re-read from the file.

    Raises:
        OutputReviewError: if the file cannot be opened as a docx, has no document
            part, or carries no ``Title`` paragraph (fail-closed — CLAUDE.md §5.6).
    """
    try:
        with zipfile.ZipFile(docx_path) as archive:
            document_xml = archive.read(_DOCUMENT_PART)
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        # fail-closed: an unreadable container or a missing document part means we
        # cannot recover the title — refuse rather than invent one.
        raise OutputReviewError(
            f"cannot read docx document part from {docx_path.name}: {type(exc).__name__}"
        ) from exc

    root = ET.fromstring(document_xml)  # nosec B314 - trusted, self-produced OOXML bytes
    for paragraph in root.iter(f"{_W}p"):
        style = paragraph.find(f"{_W}pPr/{_W}pStyle")
        if style is not None and style.get(f"{_W}val") == _TITLE_STYLE:
            # Concatenate every text run in the title paragraph (python-docx may
            # split a run, though for our specs it is one) — the full title text.
            return "".join(node.text or "" for node in paragraph.iter(f"{_W}t"))

    # fail-closed: no Title paragraph means the renderer did not emit the title we
    # would round-trip against — a defect, not a recoverable empty string.
    raise OutputReviewError(
        f"no {_TITLE_STYLE!r}-styled paragraph found in {docx_path.name}"
    )


def build_document_spec_round_trip(
    declared_title: str, docx_path: Path
) -> SpecRoundTrip:
    """Build a genuine title round-trip: spec title vs the title re-read from disk.

    Args:
        declared_title: The title the originating document spec declared.
        docx_path: The written ``.docx`` to re-read the title back out of.

    Returns:
        A :class:`SpecRoundTrip` whose ``declared_values`` is the spec title and
        ``extracted_values`` is the title recovered from the file — equal iff the
        title round-tripped intact.

    Raises:
        OutputReviewError: if the title cannot be re-read from ``docx_path``
            (propagated from :func:`extract_document_title`), or if the resulting
            maps are blank/empty (refused by :class:`SpecRoundTrip` — fail-closed).
    """
    extracted_title = extract_document_title(docx_path)  # re-read from real bytes
    return SpecRoundTrip(
        declared_values={TITLE_KEY: declared_title},
        extracted_values={TITLE_KEY: extracted_title},
    )
