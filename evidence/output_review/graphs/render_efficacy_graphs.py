"""Render the three efficacy graphs (PNG via matplotlib + interactive HTML via plotly).

Analysis-only (CLAUDE.md §3.10). Reads the MEASURED efficacy numbers from
``_measured/efficacy_metrics.json`` and renders:

* ``detection_by_panko_class`` — defect-detection rate per Panko class, Wilson-CI
  whiskers, must-block classes at 100% (EUREKA shown as out-of-floor);
* ``escape_vs_human_baseline`` — the gate's ~0 escape & false-positive rate against
  the ~86% un-reviewed-human error baseline (the motivating gap);
* ``verdict_determinism`` — unique verdict digests per case (all 1 over 3600 reviews).

Every value is read from the harness output — no magic constants.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import plotly.graph_objects as go

from evidence_chart_style import (
    GOOD,
    INK,
    LIGHT_GREY,
    MID_GREY,
    OUT_DIR,
    PLOTLY_FONT,
    RISK,
    apply_matplotlib_house_style,
    caption,
    load_efficacy,
)

_PLOTLY_KW = {"include_plotlyjs": "cdn", "full_html": True}


def _asym_err(rate: float, lo: float, hi: float) -> tuple[float, float]:
    """Asymmetric (lower, upper) error-bar lengths from a Wilson interval."""
    return (max(0.0, rate - lo), max(0.0, hi - rate))


def render_detection_by_class() -> None:
    """Bar of detection rate per Panko class with Wilson-CI whiskers (PNG + HTML)."""
    data = load_efficacy()["detection_by_panko_class"]
    classes = ["MECHANICAL", "PURE_LOGIC", "OMISSION"]
    rates = [data[c]["detection_rate"] for c in classes]
    los = [data[c]["wilson95_low"] for c in classes]
    his = [data[c]["wilson95_high"] for c in classes]
    planted = [data[c]["planted"] for c in classes]
    labels = [*classes, "EUREKA"]

    # --- PNG ---
    apply_matplotlib_house_style()
    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    x = list(range(len(classes)))
    # Clamp to >= 0: a Wilson bound can land at 0.999999… (float), making a raw
    # whisker length a tiny negative that matplotlib rejects.
    lower = [max(0.0, r - lo) for r, lo in zip(rates, los, strict=True)]
    upper = [max(0.0, hi - r) for r, hi in zip(rates, his, strict=True)]
    ax.bar(x, rates, width=0.58, color=GOOD, edgecolor=INK, linewidth=0.8, zorder=3)
    ax.errorbar(
        x, rates, yerr=[lower, upper], fmt="none", ecolor=INK, elinewidth=1.3,
        capsize=7, capthick=1.3, zorder=4,
    )
    # EUREKA: shown out-of-floor (hatched, zero height marker) so the story is honest.
    ax.bar(
        len(classes), 0.0, width=0.58, color=LIGHT_GREY, edgecolor=MID_GREY,
        hatch="///", linewidth=0.8, zorder=3,
    )
    for xi, r, n in zip(x, rates, planted, strict=True):
        ax.text(xi, r + 0.015, f"{r:.0%}\n(n={n})", ha="center", va="bottom",
                fontsize=10, fontweight="bold", color=INK)
    ax.text(len(classes), 0.02, "out of\nfloor", ha="center", va="bottom",
            fontsize=9, color=MID_GREY, style="italic")
    ax.set_xticks([*x, len(classes)])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.12)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylabel("Defect-detection rate")
    ax.set_title("Defect detection by Panko-Halverson class", loc="left")
    caption(fig, "Measured over the labelled golden set; whiskers = Wilson 95% CI. "
                 "EUREKA is the residue the deterministic floor cannot reach.")
    fig.savefig(OUT_DIR / "detection_by_panko_class.png")
    plt.close(fig)

    # --- HTML ---
    hfig = go.Figure()
    hfig.add_bar(
        x=classes, y=rates, marker_color=GOOD, marker_line_color=INK,
        marker_line_width=1,
        error_y={"type": "data", "symmetric": False,
                 "array": upper, "arrayminus": lower, "color": INK, "thickness": 1.4,
                 "width": 8},
        hovertemplate="%{x}<br>detection %{y:.1%}<extra></extra>",
        text=[f"{r:.0%} (n={n})" for r, n in zip(rates, planted, strict=True)],
        textposition="outside",
    )
    hfig.add_bar(x=["EUREKA"], y=[0.0], marker_color=LIGHT_GREY,
                 marker_pattern_shape="/", name="out of floor",
                 hovertemplate="EUREKA: out of deterministic floor<extra></extra>")
    hfig.update_layout(
        title="Defect detection by Panko-Halverson class (measured)",
        yaxis={"tickformat": ".0%", "range": [0, 1.12], "title": "Detection rate"},
        showlegend=False, template="simple_white",
        font={"family": PLOTLY_FONT, "color": INK, "size": 13},
        margin={"l": 70, "r": 30, "t": 60, "b": 50},
    )
    hfig.write_html(OUT_DIR / "detection_by_panko_class.html", **_PLOTLY_KW)


def render_escape_vs_baseline() -> None:
    """Gate escape & false-positive rate vs the ~86% un-reviewed-human baseline."""
    head = load_efficacy()["headline"]
    baseline = head["unreviewed_human_error_baseline"]
    self_est = head["human_self_estimated_error"]
    esc = head["escape_rate"]
    fp = head["false_positive_rate"]
    esc_ci = head["escape_rate_wilson95"]
    fp_ci = head["false_positive_rate_wilson95"]
    names = ["Un-reviewed human\n(actual, Panko)", "Human self-\nestimate",
             "Gate escape\nrate", "Gate false-\npositive rate"]
    vals = [baseline, self_est, esc, fp]
    colours = [RISK, MID_GREY, GOOD, GOOD]

    apply_matplotlib_house_style()
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    x = list(range(len(vals)))
    ax.bar(x, vals, width=0.6, color=colours, edgecolor=INK, linewidth=0.8, zorder=3)
    # CI whiskers on the two measured gate bars only.
    ax.errorbar([2], [esc], yerr=[[esc - esc_ci[0]], [esc_ci[1] - esc]], fmt="none",
                ecolor=INK, elinewidth=1.2, capsize=6, zorder=4)
    ax.errorbar([3], [fp], yerr=[[fp - fp_ci[0]], [fp_ci[1] - fp]], fmt="none",
                ecolor=INK, elinewidth=1.2, capsize=6, zorder=4)
    for xi, v in zip(x, vals, strict=True):
        ax.text(xi, v + 0.015, f"{v:.0%}", ha="center", va="bottom",
                fontsize=11, fontweight="bold", color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylabel("Error / escape rate")
    ax.set_title("Why the gate exists: ~0% escape vs ~86% un-reviewed error",
                 loc="left")
    caption(fig, "Baseline & self-estimate: Panko (B16 SYNTHESIS §A.1). Gate rates "
                 "measured over the golden set; whiskers = Wilson 95% CI.")
    fig.savefig(OUT_DIR / "escape_vs_human_baseline.png")
    plt.close(fig)

    hfig = go.Figure()
    hfig.add_bar(
        x=["Un-reviewed human (actual)", "Human self-estimate",
           "Gate escape rate", "Gate false-positive"],
        y=vals, marker_color=colours, marker_line_color=INK, marker_line_width=1,
        text=[f"{v:.0%}" for v in vals], textposition="outside",
        hovertemplate="%{x}<br>%{y:.1%}<extra></extra>",
    )
    hfig.update_layout(
        title="~0% gate escape rate vs ~86% un-reviewed-human error (measured)",
        yaxis={"tickformat": ".0%", "range": [0, 1.0], "title": "Error / escape rate"},
        template="simple_white", showlegend=False,
        font={"family": PLOTLY_FONT, "color": INK, "size": 13},
        margin={"l": 70, "r": 30, "t": 60, "b": 70},
    )
    hfig.write_html(OUT_DIR / "escape_vs_human_baseline.html", **_PLOTLY_KW)


def render_determinism() -> None:
    """Unique verdict digests per case — all 1 over the full repeat campaign."""
    det = load_efficacy()["determinism"]
    per_case = det["unique_digests_per_case"]
    cases = list(per_case)
    uniq = [per_case[c] for c in cases]
    runs = det["runs_per_case"]
    total = det["total_reviews"]

    apply_matplotlib_house_style()
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    y = list(range(len(cases)))
    ax.barh(y, uniq, color=GOOD, edgecolor=INK, linewidth=0.7, zorder=3, height=0.62)
    ax.axvline(2, color=RISK, linestyle="--", linewidth=1.4, zorder=2,
               label="non-determinism would be ≥ 2")
    ax.set_yticks(y)
    ax.set_yticklabels(cases, fontsize=8.0)
    ax.invert_yaxis()
    ax.set_xlim(0, 3)
    ax.set_xticks([0, 1, 2, 3])
    ax.set_xlabel(f"Unique verdict digests over {runs} repeated reviews (1 = stable)")
    ax.set_title("Verdict determinism: 1 digest per case, "
                 f"{total} reviews total", loc="left")
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    caption(fig, "Each case reviewed under a fixed injected clock; SHA-256 over the "
                 "canonical verdict JSON. All cases collapse to a single digest.")
    fig.savefig(OUT_DIR / "verdict_determinism.png")
    plt.close(fig)

    hfig = go.Figure()
    hfig.add_bar(x=uniq, y=cases, orientation="h", marker_color=GOOD,
                 marker_line_color=INK, marker_line_width=1,
                 hovertemplate="%{y}<br>%{x} unique digest(s)<extra></extra>")
    hfig.add_vline(x=2, line_color=RISK, line_dash="dash")
    hfig.update_layout(
        title=f"Verdict determinism — 1 digest/case over {total} reviews (measured)",
        xaxis={"title": f"Unique digests over {runs} reviews", "range": [0, 3]},
        yaxis={"autorange": "reversed"}, template="simple_white", showlegend=False,
        font={"family": PLOTLY_FONT, "color": INK, "size": 11},
        margin={"l": 220, "r": 30, "t": 60, "b": 50},
    )
    hfig.write_html(OUT_DIR / "verdict_determinism.html", **_PLOTLY_KW)


def main() -> None:
    """Render all three efficacy graphs to PNG + HTML."""
    render_detection_by_class()
    render_escape_vs_baseline()
    render_determinism()
    print("rendered: detection_by_panko_class, escape_vs_human_baseline, "
          "verdict_determinism (PNG + HTML)")


if __name__ == "__main__":
    main()
