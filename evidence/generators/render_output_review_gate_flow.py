"""Render the human-facing output-review gate flow diagram (PNG + HTML).

Zooms into the B16 output-review gate — the fail-closed barrier between AutoFirm's
artifact builders and any human. A built artifact is graded by N INDEPENDENT,
deterministic checks (numeric recomputation, accounting-identity, file-opens-clean,
lint, spec round-trip, visual-integrity, IBCS rubric); the findings compose a typed
``ReviewVerdict`` whose ``passed`` is DERIVED from them (a green-but-wrong verdict
cannot be manufactured). A pass admits delivery; any failure builds a structured
send-back and loops the builder until clean — acceptance never comes from the
builder's own self-assessment. Hand-authored B&W matplotlib. Analysis-only.
"""

from __future__ import annotations

from flow_diagram_primitives import (
    Node,
    connect,
    draw_band,
    draw_node,
    new_canvas,
    save_png_and_html,
)
from showcase_style import DIAGRAMS_DIR as OUT
from showcase_style import GREY_LIGHT

_W = 2.7
_H = 1.0
_OUT_NAME = "output_review_gate_flow.png"
_SAME_ROW_EPS = 0.1


def _nodes() -> list[Node]:
    """Return the builder → independent-checks → verdict → deliver/send-back nodes."""
    cols = [2.5, 6.2, 9.9, 13.6, 17.3]
    check_y, verdict_y = 6.7, 3.6
    return [
        # INDEPENDENT CHECKS row
        Node("artifact", cols[0], check_y, _W, _H, "built artifact", "xlsx/pptx/docx", GREY_LIGHT),
        Node("numeric", cols[1], check_y, _W, _H, "numeric recompute", "+ accounting identity"),
        Node("opens", cols[2], check_y, _W, _H, "file opens clean", "+ fast lint"),
        Node("roundtrip", cols[3], check_y, _W, _H, "spec round-trip", "+ visual integrity"),
        Node("rubric", cols[4], check_y, _W, _H, "IBCS rubric", "success criteria"),
        # VERDICT + DECISION row
        Node("findings", cols[0], verdict_y, _W, _H, "findings", "severity-typed"),
        Node("verdict", cols[1], verdict_y, _W, _H, "ReviewVerdict", "passed DERIVED, not claimed"),
        Node("guard", cols[2], verdict_y, _W, _H, "admission guard", "fail-closed release gate"),
        Node("sendback", cols[3], verdict_y, _W, _H, "send-back", "structured correction"),
        Node("loop", cols[4], verdict_y, _W, _H, "correction loop", "re-build until clean"),
        # OUTCOMES
        Node("deliver", cols[1], 0.9, _W * 1.4, _H, "DELIVER to human", "error-free", GREY_LIGHT),
        Node("refuse", cols[3], 0.9, _W * 1.4, _H, "REFUSE + loop", "never unverified", GREY_LIGHT),
    ]


def _edges() -> list[tuple[str, str]]:
    """Return the directed flow edges by node key."""
    return [
        ("artifact", "numeric"),
        ("numeric", "opens"),
        ("opens", "roundtrip"),
        ("roundtrip", "rubric"),
        ("rubric", "loop"),  # checks feed the verdict row (drop down)
        ("findings", "verdict"),
        ("verdict", "guard"),
        ("guard", "sendback"),
        ("sendback", "loop"),
        ("guard", "deliver"),
        ("loop", "refuse"),
    ]


def main() -> None:
    """Render the output-review gate flow as PNG + HTML."""
    fig, ax = new_canvas(17.0, 7.8)
    ax.set_xlim(-0.4, 19.3)
    ax.set_ylim(0.1, 8.6)

    draw_band(ax, (0.55, 6.0, 18.9, 7.4), "INDEPENDENT CHECKS")
    draw_band(ax, (0.55, 2.9, 18.9, 4.3), "VERDICT")

    nodes = {n.key: n for n in _nodes()}
    for node in nodes.values():
        draw_node(ax, node)

    for src_key, dst_key in _edges():
        src, dst = nodes[src_key], nodes[dst_key]
        if abs(src.cy - dst.cy) < _SAME_ROW_EPS:
            connect(ax, (src.cx + src.w / 2, src.cy), (dst.cx - dst.w / 2, dst.cy))
        else:
            connect(ax, (src.cx, src.cy - src.h / 2), (dst.cx, dst.cy + dst.h / 2))

    ax.text(
        9.45, 8.35,
        "Output-review gate — independent checks → derived verdict → deliver or send-back",
        ha="center", va="center", fontsize=15, fontweight="bold",
    )
    save_png_and_html(fig, OUT / _OUT_NAME, "AutoFirm — output-review gate flow")
    print(f"output-review gate flow: {len(nodes)} nodes -> {OUT / _OUT_NAME}")


if __name__ == "__main__":
    main()
