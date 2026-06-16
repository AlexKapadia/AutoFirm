"""Typed content spec for a Minto-structured slide deck.

What this does
--------------
Defines the immutable, validated input contract for
:mod:`autofirm.artifacts.slide_deck_builder`. A deck is a title slide plus a
sequence of content slides, each carrying an **action title** — a full-sentence
claim, not a topic label (Minto/IBCS, ``docs/research/B15-artifact-generation``
§2.2) — and a small set of MECE supporting bullets.

Why it exists / where it sits
-----------------------------
Keeping the spec separate from the renderer lets any planner build a deck and
keeps the renderer free of content logic (CLAUDE.md §3.9). The professional
craft rules that are *structurally* checkable — title is an assertion, bullet
count is bounded so one slide carries one message (Kosslyn capacity limit) — are
enforced here at construction (fail-closed — CLAUDE.md §5.6).

Security / compliance invariants upheld
---------------------------------------
``__post_init__`` refuses an empty deck, an empty/over-long title, a topic-label
title (no verb / ends in a colon), or an over-stuffed slide with
:class:`ArtifactSpecError`, so a malformed deck never reaches the renderer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from autofirm.artifacts.artifact_spec_validation_errors import ArtifactSpecError

__all__ = ["DeckSpec", "SlideSpec"]

# Capacity limit (Kosslyn / IBCS one-message-per-slide): a slide is refused if it
# carries more than this many bullets, forcing MECE decomposition rather than a
# kitchen-sink exhibit.
_MAX_BULLETS_PER_SLIDE = 6
# An action title must be a readable claim, not a heading fragment or a paragraph.
_MIN_TITLE_WORDS = 3
_MAX_TITLE_CHARS = 120


@dataclass(frozen=True, slots=True)
class SlideSpec:
    """A single content slide carrying one message.

    Args:
        action_title: A full-sentence claim (the slide's single message), e.g.
            ``"Revenue grew 32% as enterprise seats doubled"``. Must read as an
            assertion: at least :data:`_MIN_TITLE_WORDS` words and not a bare
            topic label ending in a colon.
        bullets: MECE supporting points (at least one, at most
            :data:`_MAX_BULLETS_PER_SLIDE`). Each must be non-empty.

    Raises:
        ArtifactSpecError: If the title is not a valid assertion or the bullets
            are empty / over the per-slide cap (fail-closed — CLAUDE.md §5.6).
    """

    action_title: str
    bullets: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate the slide's message and bullet discipline."""
        title = self.action_title.strip()
        if len(title) > _MAX_TITLE_CHARS:  # fail-closed: a title is a claim, not a paragraph
            raise ArtifactSpecError(
                f"action title exceeds {_MAX_TITLE_CHARS} chars: {title[:40]!r}..."
            )
        if title.endswith(":"):  # fail-closed: a colon signals a topic label, not a claim
            raise ArtifactSpecError(f"action title is a topic label, not an assertion: {title!r}")
        if len(title.split()) < _MIN_TITLE_WORDS:  # fail-closed: too short to be a claim
            raise ArtifactSpecError(
                f"action title must be a sentence (>= {_MIN_TITLE_WORDS} words): {title!r}"
            )
        if not self.bullets:  # fail-closed: a content slide needs supporting points
            raise ArtifactSpecError(f"slide {title!r} needs at least one bullet")
        if len(self.bullets) > _MAX_BULLETS_PER_SLIDE:
            raise ArtifactSpecError(
                f"slide {title!r} has {len(self.bullets)} bullets, max {_MAX_BULLETS_PER_SLIDE} "
                "(one message per slide — decompose MECE)"
            )
        for bullet in self.bullets:
            if not bullet.strip():  # fail-closed: a blank bullet is a content gap
                raise ArtifactSpecError(f"slide {title!r} has an empty bullet")


@dataclass(frozen=True, slots=True)
class DeckSpec:
    """A complete, validated deck: a title slide plus content slides.

    Args:
        title: Deck title shown on the title slide (non-empty).
        subtitle: Optional subtitle / author / date line.
        slides: Content slides in presentation order; at least one.

    Raises:
        ArtifactSpecError: If the title is empty or there are no slides
            (fail-closed — CLAUDE.md §5.6).
    """

    title: str
    slides: tuple[SlideSpec, ...]
    subtitle: str = field(default="")

    def __post_init__(self) -> None:
        """Validate deck-level structure."""
        if not self.title.strip():  # fail-closed: an untitled deck is refused
            raise ArtifactSpecError("deck title must be non-empty")
        if not self.slides:  # fail-closed: an empty deck is meaningless
            raise ArtifactSpecError("deck needs at least one content slide")
