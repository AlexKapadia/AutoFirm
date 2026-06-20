"""Render the operator cockpit control-plane flow diagram (PNG + HTML).

Zooms into the cockpit — the human operator's live terminal window onto a running
AutoFirm. Adapters bind the platform's verified public seams (org snapshot, spend,
front-door activity, kill-switch, provenance) and feed a shared append-only NDJSON
event log; the PURE core (tree projection, spend roll-up, budget thresholds,
approval-risk scoring, command parsing) derives read models that the Textual TUI
panels render. The operator's commands — questions, the kill-switch, the autonomy
dial, the approval queue — pass an auth gate and are appended back to the same log.
Hand-authored B&W matplotlib. Analysis-only.
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
_H = 1.05
_OUT_NAME = "cockpit_control_plane_flow.png"
_SAME_ROW_EPS = 0.1


def _nodes() -> list[Node]:
    """Return the platform → adapters → log → core → read-models → TUI nodes."""
    cols = [2.5, 6.2, 9.9, 13.6, 17.3]
    ingest_y, render_y = 6.7, 3.6
    return [
        # INGEST row (bind the live platform)
        Node("platform", cols[0], ingest_y, _W, _H, "platform", "verified seams", GREY_LIGHT),
        Node("adapters", cols[1], ingest_y, _W, _H, "adapters", "org · spend · front-door"),
        Node("eventlog", cols[2], ingest_y, _W, _H, "event log", "append-only NDJSON"),
        Node("core", cols[3], ingest_y, _W, _H, "pure core", "projections · spend math"),
        Node("readmodels", cols[4], ingest_y, _W, _H, "read models", "org · spend · activity"),
        # RENDER + COMMAND row
        Node("tui", cols[0], render_y, _W, _H, "Textual TUI", "live panels, no logic"),
        Node("operator", cols[1], render_y, _W, _H, "operator", "watches + commands"),
        Node("auth", cols[2], render_y, _W, _H, "auth gate", "operator authn/z"),
        Node("risk", cols[3], render_y, _W, _H, "approval risk", "score + autonomy dial"),
        Node("kill", cols[4], render_y, _W, _H, "kill-switch", "global halt control"),
        # OUTCOME
        Node("append", cols[2], 0.9, _W * 1.6, _H, "command logged", "audited to log", GREY_LIGHT),
    ]


def _edges() -> list[tuple[str, str]]:
    """Return the directed flow edges by node key."""
    return [
        ("platform", "adapters"),
        ("adapters", "eventlog"),
        ("eventlog", "core"),
        ("core", "readmodels"),
        ("readmodels", "kill"),  # ingest feeds render row (drop down)
        ("tui", "operator"),
        ("operator", "auth"),
        ("auth", "risk"),
        ("risk", "kill"),
        ("auth", "append"),
        ("kill", "append"),
    ]


def main() -> None:
    """Render the cockpit control-plane flow as PNG + HTML."""
    fig, ax = new_canvas(17.0, 7.8)
    ax.set_xlim(-0.4, 19.3)
    ax.set_ylim(0.1, 8.6)

    draw_band(ax, (0.55, 6.0, 18.9, 7.4), "INGEST")
    draw_band(ax, (0.55, 2.9, 18.9, 4.3), "RENDER + COMMAND")

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
        "Operator cockpit — bind live platform → pure projections → TUI → audited commands",
        ha="center", va="center", fontsize=15, fontweight="bold",
    )
    save_png_and_html(fig, OUT / _OUT_NAME, "AutoFirm — cockpit control-plane flow")
    print(f"cockpit control-plane flow: {len(nodes)} nodes -> {OUT / _OUT_NAME}")


if __name__ == "__main__":
    main()
