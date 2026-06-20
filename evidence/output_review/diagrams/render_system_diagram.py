"""Render the whole-system output-review flow diagram (B&W) — PNG + HTML.

Analysis-only (CLAUDE.md §3.10). One end-to-end picture of the lane: an artifact
builder emits a ReviewableArtifact → the gate (7 checks) returns a ReviewVerdict →
if it passes, the ReleaseDecisionGate authorises and the admission guard admits it to
the librarian and on to the human; if it fails, a bounded correction loop regenerates
and re-reviews, and an exhausted budget (or an unauthorised release) ends in a
fail-closed BLOCKED terminal — nothing reaches a human un-reviewed.
"""

from __future__ import annotations

from pathlib import Path

from bw_flow_diagram_toolkit import (
    arrow,
    decision,
    elbow,
    new_canvas,
    process,
    save_png_and_html,
    store,
)

OUT_DIR = Path(__file__).resolve().parent


def render_system_flow() -> None:
    """The whole-system flow: builder → gate → verdict → release → librarian → human."""
    fig, ax = new_canvas(16.0, 9.0,
                         "AutoFirm output-review lane — whole-system flow (fail-closed)")

    # --- top row: the review spine, left to right ---
    builder = process(ax, 9, 72, 15, 13,
                      "Artifact builder\n(finance / deck /\ndoc lane)")
    artifact = process(ax, 27, 72, 15, 13,
                       "ReviewableArtifact\n(by-value facts\n+ file)")
    gate = process(ax, 46, 72, 17, 14,
                   "OutputReviewGate\n7 independent checks\n→ ReviewVerdict",
                   emphasis=True)
    passed = decision(ax, 67, 72, 15, 14, "verdict\n.passed?")
    releasegate = process(ax, 88, 72, 18, 15,
                          "ReleaseDecisionGate\n.decide()\nauthorised ←\nverdict.passed",
                          emphasis=True)

    # --- delivery row: down the right, then left to the human ---
    guard = process(ax, 88, 44, 20, 12,
                    "require_authorised_release()\n— admission guard", emphasis=True)
    librarian = store(ax, 60, 44, 18, 11, "Librarian /\ndocument store")
    human = process(ax, 34, 44, 18, 11, "Human\n(owner / CEO /\ninvestor)",
                    emphasis=True)

    # --- failure handling: bounded loop + fail-closed terminal ---
    correction = process(ax, 67, 22, 28, 13,
                         "Bounded correction loop\n(send-back → re-review,\n"
                         "max_attempts)")
    refused = process(ax, 90, 11, 26, 9, "BLOCKED — never delivered\n(fail-closed)",
                      emphasis=True)

    arrow(ax, builder.right, artifact.left)
    arrow(ax, artifact.right, gate.left)
    arrow(ax, gate.right, passed.left)
    arrow(ax, passed.right, releasegate.left, label="yes")
    arrow(ax, releasegate.bottom, guard.top, label="ReleaseDecision\n(authorised)")
    arrow(ax, guard.left, librarian.right, label="authorised\n& ref ok")
    arrow(ax, librarian.left, human.right, label="delivered")
    arrow(ax, passed.bottom, correction.top, label="no")
    elbow(ax, correction.left, builder.bottom, via_x=9,
          label="regenerate & re-review")
    arrow(ax, correction.bottom, refused.left, label="budget exhausted")
    arrow(ax, guard.bottom, (90, refused.top[1]), label="unauthorised")

    ax.text(50, 2.4,
            "No artifact reaches a human un-reviewed: acceptance is the gate's derived "
            "verdict, never the builder's word. Every refusal is fail-closed; every "
            "release is audited and ref-bound.",
            ha="center", va="center", fontsize=8.2, color="#101114")
    save_png_and_html(
        fig, OUT_DIR, "system_flow_whole",
        "Whole-system output-review flow: an artifact is reviewed by the 7-check gate "
        "before any human sees it; a pass is authorised, audited and admitted to the "
        "librarian; a fail is regenerated in a bounded loop or blocked fail-closed.")


def main() -> None:
    """Render the whole-system diagram."""
    render_system_flow()
    print("rendered: system_flow_whole (PNG + HTML)")


if __name__ == "__main__":
    main()
