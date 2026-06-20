"""Render the whole-system B&W architecture diagram (PNG + HTML).

Lays the 26 platform packages out in flow order as horizontal layers — from the
deterministic foundation up through agent execution, the org/communication fabric,
the business-capability engines, the operator control plane, the one-and-only
activation/composition layer, and finally the end-to-end validation that exercises
them all on real public companies. Hand-authored with matplotlib (no graphviz
``dot`` binary on this box) for exact, clean spacing. Analysis-only.
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
from showcase_style import GREY_FAINT, GREY_LIGHT

# Grid geometry: 8 columns wide, generous gutters so nothing crowds or overlaps.
_W = 2.55  # node width
_H = 1.05  # node height
# Eight evenly-spaced column centres (≈3.05 apart → ≥0.5 horizontal gutter).
_COL = [2.0, 5.05, 8.1, 11.15, 14.2, 17.25, 20.3, 23.35]
# Horizontal centre of the whole grid (used to centre single-node bands).
_MID = (_COL[3] + _COL[4]) / 2
_OUT_NAME = "system_architecture.png"

# Band row y-centres, bottom-to-top, with ~1.45 between stacked rows in a band.
_FND = 1.7  # foundation
_EXE = 4.6  # execution
_FAB_LO, _FAB_HI = 7.5, 8.95  # fabric (two rows)
_ENG_LO, _ENG_HI = 11.85, 13.3  # engines (two rows)
_CTL = 16.2  # control plane
_ACT = 19.1  # activation
_VAL = 22.0  # validation


def _layers() -> list[tuple[str, list[Node]]]:
    """Return the (band_label, nodes) for each architecture layer, top-to-bottom."""
    return [
        (
            "VALIDATION",
            [
                Node(
                    "e2e", _MID, _VAL, _W * 2.6, _H,
                    "End-to-end validation",
                    "build + operate diverse public companies",
                    GREY_LIGHT,
                ),
            ],
        ),
        (
            "ACTIVATION",
            [
                Node("bootstrap", _COL[2], _ACT, _W, _H, "bootstrap",
                     "idempotent env converge", GREY_FAINT),
                Node("runtime", _COL[4], _ACT, _W, _H, "runtime",
                     "compose · supervise · CLI", GREY_FAINT),
            ],
        ),
        (
            "CONTROL PLANE",
            [
                Node("cockpit", _MID, _CTL, _W * 1.6, _H,
                     "cockpit", "operator terminal · kill-switch", GREY_FAINT),
            ],
        ),
        (
            "BUSINESS ENGINES",
            [
                Node("finance", _COL[0], _ENG_HI, _W, _H, "finance", "3 statements · DCF"),
                Node("decisions", _COL[1], _ENG_HI, _W, _H, "decisions", "pricing · runway"),
                Node("market_intel", _COL[2], _ENG_HI, _W, _H, "market_intel", "sense·greenlight"),
                Node("frontdoor", _COL[3], _ENG_HI, _W, _H, "frontdoor", "route human Qs"),
                Node("artifacts", _COL[4], _ENG_HI, _W, _H, "artifacts", "xlsx · pptx · docx"),
                Node("output_review", _COL[5], _ENG_HI, _W, _H, "output_review", "review gate"),
                Node("design_product", _COL[6], _ENG_HI, _W, _H, "design_product", "client UX"),
                Node("document_store", _COL[1], _ENG_LO, _W, _H, "document_store", "filed docs"),
                Node("heartbeat", _COL[3], _ENG_LO, _W, _H, "heartbeat", "recurring beats"),
                Node("flow", _COL[5], _ENG_LO, _W, _H, "flow", "work hand-offs"),
            ],
        ),
        (
            "ORG & FABRIC",
            [
                Node("org", _COL[0], _FAB_HI, _W, _H, "org", "hire · fire · re-scope"),
                Node("comms", _COL[1], _FAB_HI, _W, _H, "comms", "audited message bus"),
                Node("memory", _COL[2], _FAB_HI, _W, _H, "memory", "versioned recall"),
                Node("knowledge", _COL[3], _FAB_HI, _W, _H, "knowledge", "shared substrate"),
                Node("capabilities", _COL[4], _FAB_HI, _W, _H, "capabilities", "evolving registry"),
                Node("access", _COL[5], _FAB_HI, _W, _H, "access", "least-privilege RBAC"),
            ],
        ),
        (
            "EXECUTION",
            [
                Node("orchestration", _COL[1], _EXE, _W, _H, "orchestration", "saga/compensate"),
                Node("substrate", _COL[2], _EXE, _W, _H, "substrate", "Claude CLI sessions"),
                Node("modelgateway", _COL[4], _EXE, _W, _H, "modelgateway", "cross-model router"),
                Node("costledger", _COL[5], _EXE, _W, _H, "costledger", "exact spend ledger"),
            ],
        ),
        (
            "FOUNDATION",
            [
                Node("audit", _COL[2], _FND, _W, _H, "audit", "append-only log"),
                Node("foundation", _COL[4], _FND, _W, _H, "foundation", "money · determinism"),
            ],
        ),
    ]


def _draw_bands(ax) -> None:
    """Draw the faint layer bands behind the nodes.

    Each tuple is ``(label, y0, y1)``; the band spans the full diagram width. Short
    single-word labels are used so the rotated text always fits inside the band
    height (longer phrases were clipped); the full meaning is in the caption.
    """
    half = _H / 2 + 0.35  # padding above/below the outermost row in each band
    bands = [
        ("VALIDATION", _VAL - half, _VAL + half),
        ("ACTIVATION", _ACT - half, _ACT + half),
        ("CONTROL", _CTL - half, _CTL + half),
        ("ENGINES", _ENG_LO - half, _ENG_HI + half),
        ("FABRIC", _FAB_LO - half, _FAB_HI + half),
        ("EXECUTION", _EXE - half, _EXE + half),
        ("FOUNDATION", _FND - half, _FND + half),
    ]
    for label, y0, y1 in bands:
        draw_band(ax, (0.55, y0, 24.85, y1), label)


def main() -> None:
    """Render the whole-system architecture diagram as PNG + HTML."""
    fig, ax = new_canvas(20.5, 17.0)
    ax.set_xlim(-0.7, 25.7)
    ax.set_ylim(0.2, 23.8)

    _draw_bands(ax)
    nodes: dict[str, Node] = {}
    for _label, layer_nodes in _layers():
        for node in layer_nodes:
            draw_node(ax, node)
            nodes[node.key] = node

    # Upward data-flow spine: foundation feeds execution feeds fabric feeds engines;
    # the control plane observes the engines; activation composes the whole stack and
    # validation exercises it. Drawn as representative connectors (not every edge) so
    # the diagram reads as a clean flow rather than a hairball.
    spine = [
        ("foundation", "substrate"),
        ("audit", "orchestration"),
        ("substrate", "memory"),
        ("orchestration", "comms"),
        ("modelgateway", "capabilities"),
        ("costledger", "access"),
        ("comms", "org"),
        ("memory", "market_intel"),
        ("knowledge", "frontdoor"),
        ("org", "finance"),
        ("capabilities", "artifacts"),
        ("access", "output_review"),
        ("frontdoor", "cockpit"),
        ("artifacts", "cockpit"),
        ("cockpit", "runtime"),
        ("output_review", "runtime"),
        ("bootstrap", "runtime"),
        ("runtime", "e2e"),
    ]
    for src_key, dst_key in spine:
        src, dst = nodes[src_key], nodes[dst_key]
        connect(
            ax,
            (src.cx, src.cy + src.h / 2),
            (dst.cx, dst.cy - dst.h / 2),
        )

    ax.text(
        12.5,
        23.5,
        "AutoFirm — whole-system architecture (26 platform packages)",
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
    )
    ax.text(
        12.5,
        0.45,
        "Data flows upward: a deterministic, audited foundation → agent execution "
        "→ org & communication fabric → business engines → the operator control "
        "plane → the single activation/composition layer → end-to-end validation.",
        ha="center",
        va="center",
        fontsize=10.5,
        color="#3a3a3a",
    )
    save_png_and_html(
        fig, OUT / _OUT_NAME, "AutoFirm — whole-system architecture"
    )
    print(f"system architecture: {len(nodes)} nodes -> {OUT / _OUT_NAME}")


if __name__ == "__main__":
    main()
