"""Adversarial validation tests for the Minto slide-deck spec contract.

Proves the deck spec is fail-closed (CLAUDE.md §5.6): topic-label titles, empty
or over-stuffed slides, and empty decks are all refused at construction. Each
test targets a distinct craft rule the research mandates (action titles; one
message per slide).
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.artifacts.artifact_spec_validation_errors import ArtifactSpecError
from autofirm.artifacts.slide_deck_spec import DeckSpec, SlideSpec


def test_valid_slide_constructs() -> None:
    slide = SlideSpec("Revenue grew thirty two percent", ("a", "b"))
    assert slide.action_title.startswith("Revenue")


def test_topic_label_title_refused() -> None:
    # A colon-terminated heading is a topic label, not an assertion (Minto/IBCS).
    with pytest.raises(ArtifactSpecError, match="topic label"):
        SlideSpec("Quarterly results:", ("point one here",))


@pytest.mark.parametrize("title", ["Revenue up", "Two words", "One"])
def test_too_short_title_refused(title: str) -> None:
    with pytest.raises(ArtifactSpecError, match="sentence"):
        SlideSpec(title, ("a supporting point",))


def test_overlong_title_refused() -> None:
    with pytest.raises(ArtifactSpecError, match="exceeds"):
        SlideSpec("word " * 40, ("a point",))


def test_slide_with_no_bullets_refused() -> None:
    with pytest.raises(ArtifactSpecError, match="at least one bullet"):
        SlideSpec("This is a valid claim sentence", ())


def test_too_many_bullets_refused() -> None:
    # One message per slide (Kosslyn capacity limit): >6 bullets is refused.
    with pytest.raises(ArtifactSpecError, match="one message per slide"):
        SlideSpec("This is a valid claim sentence", tuple(f"b{i}" for i in range(7)))


def test_exactly_six_bullets_allowed() -> None:
    slide = SlideSpec("This is a valid claim sentence", tuple(f"b{i}" for i in range(6)))
    assert len(slide.bullets) == 6


@pytest.mark.parametrize("bullets", [("", "ok"), ("ok", "   ")])
def test_empty_bullet_refused(bullets: tuple[str, ...]) -> None:
    with pytest.raises(ArtifactSpecError, match="empty bullet"):
        SlideSpec("This is a valid claim sentence", bullets)


@pytest.mark.parametrize("title", ["", "   "])
def test_blank_deck_title_refused(title: str) -> None:
    with pytest.raises(ArtifactSpecError, match="deck title"):
        DeckSpec(title=title, slides=(SlideSpec("A valid claim sentence here", ("x",)),))


def test_empty_deck_refused() -> None:
    with pytest.raises(ArtifactSpecError, match="at least one content slide"):
        DeckSpec(title="Deck", slides=())


@pytest.mark.property
@given(n=st.integers(min_value=1, max_value=6))
def test_any_bullet_count_in_range_accepted(n: int) -> None:
    slide = SlideSpec("This is a valid claim sentence", tuple(f"b{i}" for i in range(n)))
    assert len(slide.bullets) == n


@pytest.mark.property
@given(n=st.integers(min_value=7, max_value=30))
def test_any_bullet_count_over_cap_refused(n: int) -> None:
    with pytest.raises(ArtifactSpecError):
        SlideSpec("This is a valid claim sentence", tuple(f"b{i}" for i in range(n)))
