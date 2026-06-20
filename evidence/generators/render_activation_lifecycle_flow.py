"""Render the activation / composition-root lifecycle flow diagram (PNG + HTML).

Zooms into the W3 activation layer — the ONE place the platform is turned on
(``autofirm.runtime``). ``autofirm up`` first converges the environment via the
idempotent bootstrapper (each step's pure ``check()`` gates its re-entrant
``apply()``, with a fail-closed degraded-mode policy), then the single composition
root wires every package into one ``Platform`` (Pure DI), the supervisor runs the
long-lived loops, and a readiness self-test proves it serves before the CLI reports
``up``. The ``doctor`` / ``status`` / ``down`` commands read the same surface.
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
_OUT_NAME = "activation_lifecycle_flow.png"
_SAME_ROW_EPS = 0.1


def _nodes() -> list[Node]:
    """Return the ordered converge → compose → supervise → prove → CLI nodes."""
    cols = [2.5, 6.2, 9.9, 13.6, 17.3]
    converge_y, compose_y = 6.6, 3.6
    return [
        # CONVERGE phase (bootstrap)
        Node("cmd", cols[0], converge_y, _W, _H, "autofirm up", "operator entrypoint", GREY_LIGHT),
        Node("check", cols[1], converge_y, _W, _H, "check()", "pure predicate · gates apply"),
        Node("apply", cols[2], converge_y, _W, _H, "apply()", "forward-only · re-entrant"),
        Node("degrade", cols[3], converge_y, _W, _H, "degraded policy", "degrade · fail-closed"),
        Node("ready_env", cols[4], converge_y, _W, _H, "env converged", "provable no-op on re-run"),
        # COMPOSE + PROVE phase (runtime)
        Node("compose", cols[0], compose_y, _W, _H, "composition root", "wire all pkgs · Pure DI"),
        Node("platform", cols[1], compose_y, _W, _H, "Platform", "one cohesive object"),
        Node("supervise", cols[2], compose_y, _W, _H, "supervisor", "run long-lived loops"),
        Node("selftest", cols[3], compose_y, _W, _H, "readiness self-test", "prove it serves"),
        Node("cli", cols[4], compose_y, _W, _H, "status / down", "read-only CLI surface"),
        # RESULT
        Node("up", cols[2], 0.9, _W * 1.5, _H, "Platform up", "supervised + proven", GREY_LIGHT),
    ]


def _edges() -> list[tuple[str, str]]:
    """Return the directed flow edges by node key."""
    return [
        ("cmd", "check"),
        ("check", "apply"),
        ("apply", "degrade"),
        ("degrade", "ready_env"),
        ("ready_env", "cli"),  # converge feeds compose row (drop down)
        ("compose", "platform"),
        ("platform", "supervise"),
        ("supervise", "selftest"),
        ("selftest", "cli"),
        ("selftest", "up"),
        ("compose", "up"),
    ]


def main() -> None:
    """Render the activation lifecycle flow as PNG + HTML."""
    fig, ax = new_canvas(17.0, 7.8)
    ax.set_xlim(-0.4, 19.3)
    ax.set_ylim(0.1, 8.6)

    draw_band(ax, (0.55, 5.9, 18.9, 7.3), "CONVERGE")
    draw_band(ax, (0.55, 2.9, 18.9, 4.3), "COMPOSE")

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
        "Activation lifecycle — `autofirm up` converges, composes, supervises, proves",
        ha="center", va="center", fontsize=15.5, fontweight="bold",
    )
    save_png_and_html(fig, OUT / _OUT_NAME, "AutoFirm — activation lifecycle flow")
    print(f"activation lifecycle flow: {len(nodes)} nodes -> {OUT / _OUT_NAME}")


if __name__ == "__main__":
    main()
