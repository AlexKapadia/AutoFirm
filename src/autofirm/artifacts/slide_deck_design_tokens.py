"""Design tokens for the AutoFirm slide-deck template.

What this does
--------------
Centralises the deliberate type, colour and spacing scale used by
:mod:`autofirm.artifacts.slide_deck_builder`. Decisions live here as named
constants so the deck has a *real* system (a chosen palette, a type ramp, a
spacing grid) instead of python-pptx defaults — the difference between a
designed deck and an AI-slop one (CLAUDE.md §3.14;
``docs/research/B15-artifact-generation`` §2.2).

Why it exists / where it sits
-----------------------------
Isolating tokens from the renderer keeps both files small and lets the template
be re-themed per company (generality — CLAUDE.md §3.9) without touching layout
logic. Values are restrained on purpose (Tufte/IBCS austerity): one ink colour,
one accent, generous margins.
"""

from __future__ import annotations

from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

__all__ = [
    "ACCENT_RULE",
    "BODY_FONT",
    "BODY_SIZE",
    "BULLET_GAP",
    "CONTENT_LEFT",
    "CONTENT_TOP",
    "CONTENT_WIDTH",
    "HEADING_FONT",
    "INK",
    "MUTED",
    "SLIDE_HEIGHT",
    "SLIDE_WIDTH",
    "SUBTITLE_SIZE",
    "TITLE_SIZE",
    "TITLE_TOP",
]

# 16:9 canvas (EMU via Inches) — the modern presentation aspect ratio.
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)


def _rgb(red: int, green: int, blue: int) -> RGBColor:
    """Construct an ``RGBColor`` (the library constructor is untyped in stubs)."""
    return RGBColor(red, green, blue)  # type: ignore[no-untyped-call]


# Restrained palette: a single near-black ink, one muted grey, one accent rule.
INK = _rgb(0x1F, 0x2A, 0x37)  # near-black for type (not pure #000 — softer)
MUTED = _rgb(0x6B, 0x72, 0x80)  # secondary / subtitle grey
ACCENT_RULE = _rgb(0xC8, 0x96, 0x2E)  # single amber accent for the title rule

# Type ramp — a deliberate scale (≈1.33 ratio), not arbitrary sizes.
HEADING_FONT = "Calibri"
BODY_FONT = "Calibri"
TITLE_SIZE = Pt(30)  # action-title size: large enough to lead, small enough to wrap claims
SUBTITLE_SIZE = Pt(18)
BODY_SIZE = Pt(18)

# Spacing grid — a single left margin and top anchor shared by every slide so
# titles and bodies align across the deck (perceptual organisation — Kosslyn).
CONTENT_LEFT = Inches(0.9)
CONTENT_WIDTH = Inches(11.5)
TITLE_TOP = Inches(0.6)
CONTENT_TOP = Inches(1.9)
BULLET_GAP = Pt(10)  # space after each bullet — breathing room, not cramped
