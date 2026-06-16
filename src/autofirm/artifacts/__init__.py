"""Professional business-artifact generation for AutoFirm.

What this package does
----------------------
Turns structured, typed *content specs* into genuinely institution-grade
business deliverables — Excel financial models (``.xlsx``), slide decks
(``.pptx``) and reports (``.docx``) — that follow published professional
standards (FAST / ICAEW for models; Minto / Zelazny / Tufte / IBCS for decks;
Minto storyline for documents) rather than dumping a grid or using library
defaults. See ``docs/research/B15-artifact-generation/SYNTHESIS.md``.

Why it exists / where it sits
-----------------------------
This is an **output/analysis tier** package (CLAUDE.md §3.10): it is the only
runtime package permitted to import the heavy OOXML libraries (``openpyxl``,
``python-pptx``, ``python-docx``) — kept in the ``artifacts`` optional-dependency
group, fenced out of the deterministic core by an import-linter contract. Each
builder takes a typed spec in and writes a single file out; given identical
inputs it produces an identical artifact (determinism — CLAUDE.md §3.6).

Security / compliance invariants upheld
---------------------------------------
Every builder is **fail-closed** (CLAUDE.md §5.6): a malformed or empty spec is
refused with :class:`ArtifactSpecError` *before* any file is written, so a half-
written or misleading deliverable can never reach a client. Specs carry only the
data the caller supplies — no network, no ambient state.
"""

from __future__ import annotations

from autofirm.artifacts.artifact_spec_validation_errors import ArtifactSpecError

__all__ = ["ArtifactSpecError"]
