"""Render the three component flow diagrams (B&W) — PNG + self-contained HTML.

Analysis-only (CLAUDE.md §3.10). Draws, strictly in black & white:

* ``gate_composition`` — the gate composing the 7 independent checks into one derived
  ReviewVerdict (the false-pass guard);
* ``correction_send_back_loop`` — the bounded correction send-back / re-review loop;
* ``release_admission_seam`` — the release authority + delivery admission guard at the
  librarian seam (the fail-closed refusal path).

Layout is hand-placed on a 0..100 canvas via the B&W toolkit so spacing is
deliberate and nothing overlaps (visually QA'd after rendering).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
from bw_flow_diagram_toolkit import (
    FAINT,
    INK,
    arrow,
    decision,
    elbow,
    new_canvas,
    process,
    save_png_and_html,
    store,
)

OUT_DIR = Path(__file__).resolve().parent

_CHECKS = [
    "ACCOUNTING_IDENTITY  —  A = L + E exact",
    "SPEC_ROUND_TRIP  —  every spec value present",
    "NUMERIC_RECOMPUTE  —  declared = recomputed",
    "FILE_OPENS_CLEAN  —  opens, no repair",
    "FAST_LINT  —  orphan / row / omission",
    "IBCS_SUCCESS  —  notation + units",
    "VISUAL_INTEGRITY  —  axis / overlap / clipping",
]


def render_gate_composition() -> None:
    """The gate fans an artifact across 7 checks → one derived, fail-closed verdict."""
    fig, ax = new_canvas(15.0, 8.6, "Output-review gate — composing 7 checks → verdict")
    artifact = process(ax, 11, 52, 17, 16,
                       "ReviewableArtifact\n(by-value facts\n+ file path)")
    gate = process(ax, 31, 52, 15, 14,
                   "OutputReviewGate\n(pure composer,\nregistry order)", emphasis=True)

    # The deterministic-floor panel holding the 7 independent checks.
    ax.add_patch(mpatches.FancyBboxPatch(
        (44, 9), 36, 80, boxstyle="round,pad=0.4,rounding_size=2.0",
        linewidth=1.4, edgecolor=INK, facecolor=FAINT, zorder=1))
    ax.text(62, 91.5, "deterministic floor — 7 independent checks", ha="center",
            va="bottom", fontsize=9.0, color=INK, style="italic")
    top, bottom = 82, 16
    step = (top - bottom) / (len(_CHECKS) - 1)
    for i, label in enumerate(_CHECKS):
        process(ax, 62, top - i * step, 33, 7.6, label)

    verdict = process(ax, 92, 52, 14, 22,
                      "ReviewVerdict\n\npassed =\nNOT any(\nBLOCKING)", emphasis=True)

    arrow(ax, artifact.right, gate.left, label="review()")
    arrow(ax, gate.right, (44, 52), label="runs each")
    arrow(ax, (80, 52), verdict.left, label="findings")
    ax.text(50, 4.4,
            "Fail-closed: a check that RAISES → one BLOCKING finding (never skipped); "
            "an empty registry is REFUSED. passed is DERIVED, never set, so a "
            "green-but-wrong verdict is structurally impossible (false-pass guard).",
            ha="center", va="center", fontsize=8.0, color=INK)
    save_png_and_html(
        fig, OUT_DIR, "gate_composition",
        "The OutputReviewGate composes seven independent deterministic checks over a "
        "by-value ReviewableArtifact and returns one ReviewVerdict whose passed flag "
        "is derived from the findings — the false-pass guard.")


def render_correction_loop() -> None:
    """The bounded send-back / re-review loop until clean or budget exhausted."""
    fig, ax = new_canvas(13.0, 8.6, "Bounded correction send-back / re-review loop")
    gate = process(ax, 24, 80, 22, 12, "OutputReviewGate.review()\n→ ReviewVerdict")
    passed = decision(ax, 24, 58, 20, 14, "verdict\n.passed?")
    release = process(ax, 70, 58, 24, 12,
                      "ReleaseDecisionGate.decide()\n→ authorised release",
                      emphasis=True)
    sendback = process(ax, 24, 36, 26, 12,
                       "build_correction_send_back()\ntargets BLOCKING findings")
    advance = process(ax, 24, 16, 26, 11,
                      "CorrectionLoopState\n.record_and_advance()  (attempt + 1)")
    exhausted = decision(ax, 70, 16, 20, 14, "budget\nexhausted?")
    stop = process(ax, 70, 36, 24, 11, "STOP — refuse\n(fail-closed, no release)",
                   emphasis=True)

    arrow(ax, gate.bottom, passed.top)
    arrow(ax, passed.right, release.left, label="yes (no BLOCKING)")
    arrow(ax, passed.bottom, sendback.top, label="no")
    arrow(ax, sendback.bottom, advance.top)
    arrow(ax, advance.right, exhausted.left)
    arrow(ax, exhausted.top, stop.bottom)
    ax.text(65.5, 26.5, "yes", ha="right", va="center", fontsize=8.0, color=INK,
            style="italic")
    # Feedback: not exhausted → regenerate the artifact and re-review.
    elbow(ax, exhausted.right, gate.right, via_x=92,
          label="no → regenerate & re-review")
    ax.text(50, 4.2,
            "max_attempts is bounded (≥ 1) and enforced at construction; the loop "
            "can never run unbounded — exhaustion refuses delivery, fail-closed.",
            ha="center", va="center", fontsize=8.0, color=INK)
    save_png_and_html(
        fig, OUT_DIR, "correction_send_back_loop",
        "A failing verdict drives a bounded correction loop: a send-back targets the "
        "BLOCKING findings, the attempt counter advances, and re-review repeats until "
        "the artifact is clean or the budget is exhausted (then delivery is refused).")


def render_release_admission_seam() -> None:
    """Release authority + the delivery admission guard's fail-closed refusal path."""
    fig, ax = new_canvas(13.0, 9.0, "Release authority + delivery admission guard")
    verdict = process(ax, 22, 88, 26, 10, "final ReviewVerdict  (passed derived)")
    rgate = process(ax, 22, 68, 34, 14,
                    "ReleaseDecisionGate.decide()\nauthorised ← verdict.passed\n"
                    "+ append-only audit write", emphasis=True)
    rdecision = process(ax, 22, 48, 26, 11,
                        "ReleaseDecision\n(frozen, authorised | denied)")
    guard = process(ax, 22, 31, 34, 13,
                    "require_authorised_release(\ndecision, expected_artifact_ref)\n"
                    "— FIRST statement of the seam", emphasis=True)
    librarian = store(ax, 22, 10, 28, 9, "Librarian / document\nstore (artifact filed)")
    refused = process(ax, 74, 28, 24, 14, "DELIVERY REFUSED\n(fail-closed)",
                      emphasis=True)

    arrow(ax, verdict.bottom, rgate.top)
    arrow(ax, rgate.bottom, rdecision.top, label="audit ok")
    arrow(ax, rdecision.bottom, guard.top, label="passed to seam")
    arrow(ax, guard.bottom, librarian.top, label="authorised & ref matches")
    arrow(ax, guard.right, refused.left)
    ax.text(56, 36.5,
            "decision = None\nor not authorised\nor ref mismatch (swap)",
            ha="center", va="bottom", fontsize=7.8, color=INK, style="italic",
            linespacing=1.3)
    ax.text(50, 1.6,
            "An unaudited release is forbidden: if the audit write raises, decide() "
            "raises too. The guard runs BEFORE any store mutation, so a refusal has "
            "no side effects (anti-swap binding by artifact_ref).",
            ha="center", va="center", fontsize=8.0, color=INK)
    save_png_and_html(
        fig, OUT_DIR, "release_admission_seam",
        "The ReleaseDecisionGate derives authorisation from the verdict and audits it; "
        "the delivery admission guard refuses filing unless an authorised, "
        "ref-matching ReleaseDecision is present — fail-closed on any of three checks.")


def main() -> None:
    """Render all three component diagrams."""
    render_gate_composition()
    render_correction_loop()
    render_release_admission_seam()
    print("rendered: gate_composition, correction_send_back_loop, "
          "release_admission_seam (PNG + HTML)")


if __name__ == "__main__":
    main()
