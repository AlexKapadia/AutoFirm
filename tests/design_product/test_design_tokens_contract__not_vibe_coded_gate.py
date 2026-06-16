"""Token-contract tests: a real scale + AA-accessible palette, or refusal.

Proves the §3.14 "real type+spacing+motion scale, never vibe-coded" rule is a
hard construction gate, not advice: a single-value scale, a non-ascending or
non-positive ladder, an empty/duplicate palette, or a sub-AA on-color pairing are
each REFUSED. Includes Hypothesis properties asserting (1) any scale shorter than
MIN_SCALE_STEPS is always rejected and any strictly-ascending positive ladder of
>= MIN_SCALE_STEPS is always accepted, and (2) wcag_contrast_ratio is symmetric,
bounded in [1, 21], and exactly the WCAG formula on known anchors. Synthetic
only; no network.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from autofirm.design_product.design_tokens_contract import (
    MIN_SCALE_STEPS,
    MIN_TEXT_CONTRAST_RATIO,
    ColorRole,
    DesignTokenScales,
    relative_luminance,
    wcag_contrast_ratio,
)

# A known-good accessible role (black text on white surface == 21:1) reused below.
_ACCESSIBLE_ROLE = ColorRole(name="surface", color=(255, 255, 255), on_color=(0, 0, 0))


def _valid_scales(**overrides: object) -> DesignTokenScales:
    base: dict[str, object] = {
        "type_scale_px": (12.0, 16.0, 24.0),
        "spacing_scale_px": (4.0, 8.0, 16.0),
        "motion_scale_ms": (100.0, 200.0, 300.0),
        "color_roles": (_ACCESSIBLE_ROLE,),
    }
    base.update(overrides)
    return DesignTokenScales(**base)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# WCAG contrast maths — exact anchors (zero numerical error, §3.11).           #
# --------------------------------------------------------------------------- #


def test_contrast_black_on_white_is_exactly_21() -> None:
    # The WCAG formula's hard upper bound: pure black vs pure white == 21:1.
    assert wcag_contrast_ratio((0, 0, 0), (255, 255, 255)) == pytest.approx(21.0, abs=1e-9)


def test_contrast_identical_colors_is_exactly_1() -> None:
    # Identical colors have zero contrast (ratio 1.0) — the formula's lower bound.
    assert wcag_contrast_ratio((123, 45, 200), (123, 45, 200)) == pytest.approx(1.0, abs=1e-9)


def test_relative_luminance_white_is_one_black_is_zero() -> None:
    assert relative_luminance((255, 255, 255)) == pytest.approx(1.0, abs=1e-9)
    assert relative_luminance((0, 0, 0)) == pytest.approx(0.0, abs=1e-9)


@given(
    fg=st.tuples(st.integers(0, 255), st.integers(0, 255), st.integers(0, 255)),
    bg=st.tuples(st.integers(0, 255), st.integers(0, 255), st.integers(0, 255)),
)
def test_contrast_is_symmetric_and_bounded(
    fg: tuple[int, int, int], bg: tuple[int, int, int]
) -> None:
    # Property: contrast is order-independent and always within the WCAG range.
    ratio = wcag_contrast_ratio(fg, bg)
    assert wcag_contrast_ratio(bg, fg) == pytest.approx(ratio, rel=1e-12)
    assert 1.0 - 1e-9 <= ratio <= 21.0 + 1e-9


# --------------------------------------------------------------------------- #
# ColorRole accessibility gate.                                                #
# --------------------------------------------------------------------------- #


def test_color_role_below_aa_floor_is_refused() -> None:
    # Light-grey on white is well under 4.5:1 — must be refused (a11y-by-construction).
    with pytest.raises(ValidationError, match="below the WCAG AA text floor"):
        ColorRole(name="faint", color=(255, 255, 255), on_color=(240, 240, 240))


def test_color_role_at_floor_accepted_one_step_lighter_refused() -> None:
    # Boundary on/just-over/just-under the 4.5:1 floor against a white background.
    # Greys get LIGHTER as the value rises, so contrast DROPS as grey rises: find
    # the lightest grey still passing; the next grey up must drop below the floor.
    passing_grey = max(
        grey
        for grey in range(256)
        if wcag_contrast_ratio((grey, grey, grey), (255, 255, 255)) >= MIN_TEXT_CONTRAST_RATIO
    )
    # On the floor (or just over): accepted.
    ColorRole(name="ok", color=(255, 255, 255), on_color=(passing_grey,) * 3)
    # Exactly one channel-step lighter drops under the floor: refused (fail-closed).
    just_under = passing_grey + 1
    assert (
        wcag_contrast_ratio((just_under,) * 3, (255, 255, 255)) < MIN_TEXT_CONTRAST_RATIO
    )
    with pytest.raises(ValidationError):
        ColorRole(name="bad", color=(255, 255, 255), on_color=(just_under,) * 3)


def test_color_role_empty_name_and_out_of_range_channel_refused() -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        ColorRole(name="   ", color=(255, 255, 255), on_color=(0, 0, 0))
    with pytest.raises(ValidationError):
        ColorRole(name="x", color=(256, 0, 0), on_color=(0, 0, 0))  # channel > 255


# --------------------------------------------------------------------------- #
# Scale gate — the not-vibe-coded core.                                        #
# --------------------------------------------------------------------------- #


def test_valid_token_scales_build_and_are_frozen() -> None:
    scales = _valid_scales()
    assert scales.model_config.get("frozen") is True
    with pytest.raises(ValidationError):  # frozen: no mutation
        scales.type_scale_px = (1.0, 2.0, 3.0)


@pytest.mark.parametrize("field", ["type_scale_px", "spacing_scale_px", "motion_scale_ms"])
def test_single_value_scale_is_refused(field: str) -> None:
    # The exact AI-slop default: one font size / one margin. Must be refused.
    with pytest.raises(ValidationError, match="real scale needs"):
        _valid_scales(**{field: (16.0,)})


@pytest.mark.parametrize("field", ["type_scale_px", "spacing_scale_px", "motion_scale_ms"])
def test_non_ascending_scale_is_refused(field: str) -> None:
    with pytest.raises(ValidationError, match="strictly ascending"):
        _valid_scales(**{field: (16.0, 16.0, 24.0)})  # equal adjacent -> not ascending


@pytest.mark.parametrize("field", ["type_scale_px", "spacing_scale_px", "motion_scale_ms"])
def test_non_positive_scale_step_is_refused(field: str) -> None:
    with pytest.raises(ValidationError, match="strictly positive"):
        _valid_scales(**{field: (0.0, 8.0, 16.0)})


def test_empty_palette_is_refused() -> None:
    with pytest.raises(ValidationError, match="at least one semantic color role"):
        _valid_scales(color_roles=())


def test_duplicate_color_role_names_refused() -> None:
    dup = ColorRole(name="surface", color=(0, 0, 0), on_color=(255, 255, 255))
    with pytest.raises(ValidationError, match="unique"):
        _valid_scales(color_roles=(_ACCESSIBLE_ROLE, dup))


@given(n=st.integers(min_value=0, max_value=MIN_SCALE_STEPS - 1))
def test_property_any_too_short_scale_is_rejected(n: int) -> None:
    # Property: ANY ladder shorter than the minimum is rejected, never accepted.
    short = tuple(float(i + 1) for i in range(n))
    with pytest.raises(ValidationError):
        _valid_scales(type_scale_px=short)


@given(
    steps=st.lists(
        st.floats(min_value=1.0, max_value=1e6, allow_nan=False, allow_infinity=False),
        min_size=MIN_SCALE_STEPS,
        max_size=12,
        unique=True,
    )
)
def test_property_any_ascending_positive_ladder_is_accepted(steps: list[float]) -> None:
    # Property: ANY strictly-ascending positive ladder of >= MIN_SCALE_STEPS builds.
    ladder = tuple(sorted(steps))
    scales = _valid_scales(type_scale_px=ladder)
    assert scales.type_scale_px == ladder
