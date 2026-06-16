"""The design-token contract: a REAL color/type/spacing/motion scale, gated.

What this does
--------------
Defines :class:`DesignTokenScales` — the typed, validated design tokens a client
brief must carry. It turns CLAUDE.md §2/§3.14's "demand a **real type + spacing
scale**" and "ban the AI-slop signature" rules into a construction-time gate: a
token set is refused unless it declares a genuine, multi-step **type scale** and
**spacing scale**, a real **color palette** with accessibility-checkable on-color
pairings, and a **motion scale**. A brief with one font size and one margin (the
vibe-coded default) cannot be built.

Why it exists / where it sits
-----------------------------
Per ``docs/research/B13-product-and-design/SYNTHESIS.md`` §2-3 (token-first
design system, sources 07 W3C DTCG + 08 Material 3 three tiers), tokens are the
interoperable, lint-able contract that defeats random-hex / single-margin AI
slop. This is the lowest layer of :mod:`autofirm.design_product`: the design
brief composes these scales; nothing here depends back on the brief.

Security / compliance invariants upheld
---------------------------------------
* **Not-vibe-coded gate (fail-closed, CLAUDE.md §3.14):** each scale must have at
  least :data:`MIN_SCALE_STEPS` distinct, ordered steps — a single value is not a
  "scale" and is refused, so a real hierarchy is mandatory by construction.
* **Accessibility-by-construction (CLAUDE.md §4.9 / SYNTHESIS 07-08):** every
  color role declares an on-color pairing meeting a minimum WCAG contrast ratio
  (:data:`MIN_TEXT_CONTRAST_RATIO`, the WCAG 2.2 AA 4.5:1 normal-text floor);
  a pairing below the floor is refused.
* **Deterministic:** validation is a pure function of the inputs (no ambient
  state, no clock), so the same token set is always judged the same way.
"""

from __future__ import annotations

from itertools import pairwise

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

__all__ = [
    "MIN_SCALE_STEPS",
    "MIN_TEXT_CONTRAST_RATIO",
    "ColorRole",
    "DesignTokenScales",
    "relative_luminance",
    "wcag_contrast_ratio",
]

# Max value of an 8-bit sRGB channel (0..255). Named so the boundary check below
# reads as a real bound rather than a magic number.
_MAX_CHANNEL = 255

# WCAG sRGB linearisation knee: below this normalised channel value the transfer
# function is linear, above it the gamma curve applies (exact spec constant).
_SRGB_LINEAR_KNEE = 0.03928

# A "scale" with fewer than this many distinct steps is not a scale at all — it is
# the single-value AI-slop default the §3.14 bar bans. Three steps is the minimum
# that expresses a small/medium/large hierarchy.
MIN_SCALE_STEPS = 3

# WCAG 2.2 AA contrast floor for normal-size body text (1.4.3): a text/background
# pairing below 4.5:1 fails AA and is refused (accessibility-by-construction).
MIN_TEXT_CONTRAST_RATIO = 4.5


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """Return the WCAG relative luminance of an 8-bit sRGB color in ``[0, 1]``.

    Implements the WCAG 2.x definition exactly (W3C, *Web Content Accessibility
    Guidelines 2.2*, relative-luminance formula): each channel is normalised to
    ``[0, 1]``, linearised, then weighted ``0.2126 R + 0.7152 G + 0.0722 B``.

    Args:
        rgb: An ``(r, g, b)`` triple, each channel an integer in ``0..255``.

    Returns:
        The relative luminance, used by :func:`wcag_contrast_ratio`.
    """

    def _linearise(channel: int) -> float:
        c = channel / 255.0
        # WCAG piecewise sRGB linearisation (exact constants from the spec).
        return c / 12.92 if c <= _SRGB_LINEAR_KNEE else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (_linearise(channel) for channel in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def wcag_contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    """Return the WCAG contrast ratio between two sRGB colors (``1.0``..``21.0``).

    Exact WCAG 2.2 definition (1.4.3): ``(L_lighter + 0.05) / (L_darker + 0.05)``.
    Symmetric in its arguments; identical colors give ``1.0``, black-on-white ``21.0``.
    """
    l_fg, l_bg = relative_luminance(fg), relative_luminance(bg)
    lighter, darker = max(l_fg, l_bg), min(l_fg, l_bg)
    return (lighter + 0.05) / (darker + 0.05)


class ColorRole(BaseModel):
    """One semantic color role plus the on-color it is paired with for text.

    A role (e.g. "surface", "primary") carries its own color and the color text
    is drawn ON it; the pairing must clear the WCAG AA text floor so the palette
    is accessible by construction rather than by later audit.
    """

    model_config = ConfigDict(frozen=True)

    name: str  # semantic role name (e.g. "surface", "primary") — not a raw hex
    color: tuple[int, int, int]  # the role's sRGB color
    on_color: tuple[int, int, int]  # sRGB color of text/icons drawn on `color`

    @field_validator("name")
    @classmethod
    def _name_non_empty(cls, value: str) -> str:
        # fail-closed: an unnamed color role is a raw hex with no semantics — the
        # opposite of a token. Refuse it (§3.14 token-first).
        if not value.strip():
            raise ValueError("color role name must be non-empty (semantic token)")
        return value

    @field_validator("color", "on_color")
    @classmethod
    def _channels_in_range(cls, value: tuple[int, int, int]) -> tuple[int, int, int]:
        # fail-closed: an out-of-range channel is an invalid color and would make
        # the contrast calculation meaningless. Refuse it at the boundary.
        if any(not 0 <= channel <= _MAX_CHANNEL for channel in value):
            raise ValueError("color channels must each be in 0..255")
        return value

    @model_validator(mode="after")
    def _pairing_meets_contrast_floor(self) -> ColorRole:
        ratio = wcag_contrast_ratio(self.on_color, self.color)
        # fail-closed (accessibility-by-construction, §4.9): a pairing below the AA
        # text floor would ship inaccessible text. Refuse the role, don't warn.
        if ratio < MIN_TEXT_CONTRAST_RATIO:
            raise ValueError(
                f"color role {self.name!r}: on-color contrast {ratio:.2f}:1 is below "
                f"the WCAG AA text floor {MIN_TEXT_CONTRAST_RATIO}:1"
            )
        return self


class DesignTokenScales(BaseModel):
    """A validated set of design-token scales: a real hierarchy, not a single value.

    Construction is fail-closed: each numeric scale must declare at least
    :data:`MIN_SCALE_STEPS` distinct, strictly-ascending positive steps (a genuine
    type/spacing/motion ladder), and at least one accessible color role — turning
    the §3.14 "real scale, never vibe-coded" rule into a checkable contract.
    """

    model_config = ConfigDict(frozen=True)

    type_scale_px: tuple[float, ...]  # font-size ladder in px (small -> large)
    spacing_scale_px: tuple[float, ...]  # spacing ladder in px (tight -> loose)
    motion_scale_ms: tuple[float, ...]  # motion-duration ladder in ms (fast -> slow)
    color_roles: tuple[ColorRole, ...]  # semantic palette, each AA-accessible

    @field_validator("type_scale_px", "spacing_scale_px", "motion_scale_ms")
    @classmethod
    def _is_a_real_ascending_scale(cls, value: tuple[float, ...]) -> tuple[float, ...]:
        # fail-closed (§3.14 not-vibe-coded): a single value is not a scale, and a
        # non-ascending or non-positive ladder is not a deliberate hierarchy.
        if len(value) < MIN_SCALE_STEPS:
            raise ValueError(
                f"a real scale needs >= {MIN_SCALE_STEPS} steps (a single value is "
                f"the AI-slop default), got {len(value)}"
            )
        if any(step <= 0 for step in value):
            raise ValueError("scale steps must be strictly positive")
        if any(later <= earlier for earlier, later in pairwise(value)):
            raise ValueError("scale steps must be strictly ascending (an ordered ladder)")
        return value

    @field_validator("color_roles")
    @classmethod
    def _has_named_palette(cls, value: tuple[ColorRole, ...]) -> tuple[ColorRole, ...]:
        # fail-closed: a brief with no color roles has no palette to lint against,
        # and duplicate role names make the palette ambiguous. Refuse both.
        if not value:
            raise ValueError("at least one semantic color role is required (a real palette)")
        names = [role.name for role in value]
        if len(set(names)) != len(names):
            raise ValueError("color role names must be unique (unambiguous token map)")
        return value
