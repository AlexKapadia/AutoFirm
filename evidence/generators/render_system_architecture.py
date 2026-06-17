"""Render the whole-system B&W architecture diagram (PNG + HTML).

Lays the 18 platform packages out in flow order as horizontal layers — from the
deterministic foundation up through the agent substrate, the org/communication
fabric, the business-capability engines, and finally the end-to-end validation
that exercises them all on real public companies. Hand-authored with matplotlib
(no graphviz ``dot`` binary on this box) for exact, clean spacing. Analysis-only.
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

# Grid geometry: 6 columns wide, generous gutters so nothing crowds or overlaps.
_W = 2.7  # node width
_H = 1.05  # node height
_COL = [1.9, 4.9, 7.9, 10.9, 13.9, 16.9]  # column centres
_OUT_NAME = "system_architecture.png"


def _layers() -> list[tuple[str, float, list[Node]]]:
    """Return the (band_label, band_y_centre, nodes) for each architecture layer."""
    return [
        (
            "VALIDATION",
            13.0,
            [
                Node(
                    "e2e",
                    _COL[2],
                    13.0,
                    _W * 2.4,
                    _H,
                    "End-to-end validation",
                    "build + operate 4 public companies",
                    GREY_LIGHT,
                ),
            ],
        ),
        (
            "BUSINESS ENGINES",
            10.4,
            [
                Node("finance", _COL[0], 10.9, _W, _H, "finance", "3 statements · DCF"),
                Node("decisions", _COL[1], 10.9, _W, _H, "decisions", "pricing · runway"),
                Node("market_intel", _COL[2], 10.9, _W, _H, "market_intel", "sense · green-light"),
                Node("frontdoor", _COL[3], 10.9, _W, _H, "frontdoor", "route human Qs"),
                Node("artifacts", _COL[4], 10.9, _W, _H, "artifacts", "xlsx · pptx · docx"),
                Node("design_product", _COL[5], 10.9, _W, _H, "design_product", "client UX"),
                Node("document_store", _COL[1], 9.6, _W, _H, "document_store", "filed docs"),
                Node("heartbeat", _COL[3], 9.6, _W, _H, "heartbeat", "recurring beats"),
                Node("flow", _COL[4], 9.6, _W, _H, "flow", "work hand-offs"),
            ],
        ),
        (
            "ORG & FABRIC",
            7.0,
            [
                Node("org", _COL[0], 7.0, _W, _H, "org", "hire · fire · re-scope"),
                Node("comms", _COL[1], 7.0, _W, _H, "comms", "audited message bus"),
                Node("memory", _COL[2], 7.0, _W, _H, "memory", "versioned recall"),
                Node("access", _COL[3], 7.0, _W, _H, "access", "least-privilege RBAC"),
            ],
        ),
        (
            "EXECUTION",
            4.4,
            [
                Node("orchestration", _COL[1], 4.4, _W, _H, "orchestration", "saga / compensation"),
                Node("substrate", _COL[2], 4.4, _W, _H, "substrate", "Claude CLI sessions"),
            ],
        ),
        (
            "FOUNDATION",
            1.8,
            [
                Node("audit", _COL[1], 1.8, _W, _H, "audit", "append-only log"),
                Node("foundation", _COL[2], 1.8, _W, _H, "foundation", "money · determinism"),
            ],
        ),
    ]


def _draw_bands(ax) -> None:
    """Draw the five faint layer bands behind the nodes."""
    # Short single-word band labels so the rotated text always fits inside its
    # band height (longer phrases were clipped); the full meaning is in the caption.
    bands = [
        ("VALIDATION", 12.30, 13.70),
        ("ENGINES", 8.95, 11.55),
        ("FABRIC", 6.30, 7.70),
        ("EXECUTION", 3.70, 5.10),
        ("FOUNDATION", 1.10, 2.50),
    ]
    for label, y0, y1 in bands:
        draw_band(ax, (0.55, y0, 18.85, y1), label)


def main() -> None:
    """Render the whole-system architecture diagram as PNG + HTML."""
    fig, ax = new_canvas(16.5, 12.5)
    ax.set_xlim(-0.6, 19.4)
    ax.set_ylim(0.6, 14.2)

    _draw_bands(ax)
    nodes: dict[str, Node] = {}
    for _label, _y, layer_nodes in _layers():
        for node in layer_nodes:
            draw_node(ax, node)
            nodes[node.key] = node

    # Upward data-flow spine: foundation feeds execution feeds fabric feeds engines
    # feeds validation. Drawn as representative connectors (not every edge) so the
    # diagram reads as a clean flow rather than a hairball.
    spine = [
        ("foundation", "substrate"),
        ("audit", "orchestration"),
        ("substrate", "memory"),
        ("orchestration", "comms"),
        ("comms", "org"),
        ("org", "finance"),
        ("memory", "market_intel"),
        ("access", "frontdoor"),
        ("finance", "e2e"),
        ("market_intel", "e2e"),
        ("frontdoor", "e2e"),
    ]
    for src_key, dst_key in spine:
        src, dst = nodes[src_key], nodes[dst_key]
        connect(
            ax,
            (src.cx, src.cy + src.h / 2),
            (dst.cx, dst.cy - dst.h / 2),
        )

    ax.text(
        9.7,
        14.0,
        "AutoFirm — whole-system architecture (18 platform packages)",
        ha="center",
        va="center",
        fontsize=17,
        fontweight="bold",
    )
    ax.text(
        9.7,
        0.75,
        "Data flows upward: a deterministic, audited foundation → agent execution "
        "→ org & communication fabric → business engines → end-to-end validation.",
        ha="center",
        va="center",
        fontsize=9.5,
        color="#3a3a3a",
    )
    save_png_and_html(
        fig, OUT / _OUT_NAME, "AutoFirm — whole-system architecture"
    )
    print(f"system architecture: {len(nodes)} nodes -> {OUT / _OUT_NAME}")


if __name__ == "__main__":
    main()
