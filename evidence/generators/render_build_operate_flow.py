"""Render the build-&-operate component flow diagram (PNG + HTML).

Zooms into the headline capability: how AutoFirm takes one public-data company
through its isolated, deletable workspace — BUILD (found the org, detect a gap and
auto-hire, wire comms, file documents) then OPERATE (articulate the 3 financial
statements + DCF, make explainable pricing/runway decisions, sense the market and
green-light, route the owner's question, generate an investor artifact) and emit a
structured, asserted result. Hand-authored B&W matplotlib. Analysis-only.
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
from showcase_style import GREY_LIGHT, PAPER

_W = 2.6
_H = 1.0
_OUT_NAME = "build_operate_flow.png"
# Two nodes count as "same row" if their centres are within this y-tolerance.
_SAME_ROW_EPS = 0.1


def _nodes() -> list[Node]:
    """Return the ordered build → operate → result node sequence."""
    # Build row (y=5.4) and operate row (y=2.6); columns evenly spaced.
    cols = [2.4, 5.6, 8.8, 12.0, 15.2]
    build_y, op_y = 6.4, 3.4
    return [
        # BUILD phase
        Node(
            "workspace", cols[0], build_y, _W, _H,
            "Isolated workspace", "deletable .autofirm/", PAPER,
        ),
        Node("org", cols[1], build_y, _W, _H, "Found org", "hierarchy stood up"),
        Node("gap", cols[2], build_y, _W, _H, "Detect gap", "auto-create + hire"),
        Node("comms", cols[3], build_y, _W, _H, "Wire comms", "audited message bus"),
        Node("docs", cols[4], build_y, _W, _H, "File documents", "catalogued deliverable"),
        # OPERATE phase
        Node("finance", cols[0], op_y, _W, _H, "Finance", "3 statements + DCF"),
        Node("decisions", cols[1], op_y, _W, _H, "Decisions", "pricing + runway"),
        Node("market", cols[2], op_y, _W, _H, "Market intel", "sense + green-light"),
        Node("frontdoor", cols[3], op_y, _W, _H, "Front door", "route owner question"),
        Node("artifact", cols[4], op_y, _W, _H, "Artifact", "investor-ready output"),
        # RESULT
        Node(
            "result", cols[2], 0.7, _W * 1.5, _H,
            "Structured result", "every feature asserted", GREY_LIGHT,
        ),
    ]


def _edges() -> list[tuple[str, str]]:
    """Return the directed flow edges by node key."""
    return [
        ("workspace", "org"),
        ("org", "gap"),
        ("gap", "comms"),
        ("comms", "docs"),
        # build -> operate (drop down into the operate row)
        ("docs", "artifact"),
        ("finance", "decisions"),
        ("decisions", "market"),
        ("market", "frontdoor"),
        ("frontdoor", "artifact"),
        # operate -> result
        ("artifact", "result"),
        ("finance", "result"),
    ]


def main() -> None:
    """Render the build-&-operate component flow as PNG + HTML."""
    fig, ax = new_canvas(15.5, 7.6)
    ax.set_xlim(-0.4, 17.2)
    ax.set_ylim(0.0, 8.4)

    draw_band(ax, (0.55, 5.7, 16.7, 7.1), "BUILD")
    draw_band(ax, (0.55, 2.7, 16.7, 4.1), "OPERATE")

    nodes = {n.key: n for n in _nodes()}
    for node in nodes.values():
        draw_node(ax, node)

    for src_key, dst_key in _edges():
        src, dst = nodes[src_key], nodes[dst_key]
        if abs(src.cy - dst.cy) < _SAME_ROW_EPS:  # same row → horizontal connector
            connect(ax, (src.cx + src.w / 2, src.cy), (dst.cx - dst.w / 2, dst.cy))
        else:  # different row → vertical drop
            connect(ax, (src.cx, src.cy - src.h / 2), (dst.cx, dst.cy + dst.h / 2))

    ax.text(
        8.4,
        8.15,
        "Build & operate one company — per-company component flow",
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
    )
    save_png_and_html(fig, OUT / _OUT_NAME, "AutoFirm — build & operate flow")
    print(f"build-operate flow: {len(nodes)} nodes -> {OUT / _OUT_NAME}")


if __name__ == "__main__":
    main()
