"""Run the deterministic gate over the labelled golden corpus; emit measured numbers.

What this does (deliverable 1, CLAUDE.md §3.10)
-----------------------------------------------
Builds the labelled synthetic corpus, runs the REAL default output-review gate over
every case, and computes — from the verdicts, never by hand:

* **defect-detection rate per Panko-Halverson class** (MECHANICAL / PURE_LOGIC /
  OMISSION; EUREKA is out of the deterministic floor) — target ~100% on the
  must-block classes;
* **escape / false-pass rate** on planted defects — target 0 (a planted defect that
  the gate let PASS is the exact failure this lane exists to prevent);
* **false-positive rate** on the known-good controls — target 0;
* **determinism** — each case reviewed ``_DETERMINISM_RUNS`` times under a fixed
  injected clock; the verdict JSON must hash identically every run.

It writes the numbers to ``_measured/efficacy_metrics.json`` and a per-case
``_measured/per_case.csv`` so the stats page and every graph read MEASURED data, not
magic constants. The gate it runs is the production gate from
``autofirm.output_review`` — the probe is the only injected collaborator, and it
opens real (synthetic) bytes, so FILE_OPENS_CLEAN is genuinely exercised.

Run
---
    python evidence/output_review/golden_set/run_efficacy_harness.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
import tempfile
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

# Flat sibling imports: put this script's directory on sys.path (matches the
# existing evidence/generators pattern; keeps evidence/ a non-package tree).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ooxml_file_open_probe import OoxmlFileOpenProbe  # noqa: E402
from synthetic_golden_corpus import GoldenCase, build_corpus  # noqa: E402

from autofirm.output_review import (  # noqa: E402
    DefectClass,
    ReviewVerdict,
    build_default_output_review_gate,
)

# Repeats used to MEASURE determinism (not to prove a constant): the same artifact +
# fixed clock must hash to one verdict every time. 200 is plenty to catch any
# nondeterminism (dict ordering, set iteration) while staying sub-second.
_DETERMINISM_RUNS = 200

# Fixed injected clock so reviewed_at never varies between runs (the gate never reads
# the wall clock). Determinism is then a property of the gate logic alone.
_FIXED_CLOCK = datetime(2026, 1, 1, tzinfo=UTC)

_MEASURED_DIR = Path(__file__).resolve().parent.parent / "_measured"


def _verdict_digest(verdict: ReviewVerdict) -> str:
    """A stable SHA-256 over the verdict's canonical JSON (determinism probe)."""
    payload = verdict.model_dump_json()  # pydantic canonical serialisation
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score 95% CI for a binomial proportion (robust at p near 0/1).

    Chosen over the normal approximation because the gate's rates sit at the
    boundaries (0 and 1), where Wald intervals are degenerate (CLAUDE.md §3.10
    peer-reviewed-standard stats). Returns ``(low, high)`` clamped to [0, 1].
    """
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    z2 = z * z
    denom = 1.0 + z2 / total
    centre = (p + z2 / (2 * total)) / denom
    margin = (z * math.sqrt((p * (1 - p) + z2 / (4 * total)) / total)) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def _review_all(cases: list[GoldenCase]) -> dict[str, ReviewVerdict]:
    """Review every case once with the production gate; return case_id -> verdict."""
    gate = build_default_output_review_gate(OoxmlFileOpenProbe(), lambda: _FIXED_CLOCK)
    return {case.case_id: gate.review(case.artifact) for case in cases}


def _measure_determinism(cases: list[GoldenCase]) -> dict[str, object]:
    """Re-review every case N times; confirm one unique verdict digest per case."""
    gate = build_default_output_review_gate(OoxmlFileOpenProbe(), lambda: _FIXED_CLOCK)
    unique_per_case: dict[str, int] = {}
    for case in cases:
        digests = {
            _verdict_digest(gate.review(case.artifact))
            for _ in range(_DETERMINISM_RUNS)
        }
        unique_per_case[case.case_id] = len(digests)
    stable = all(n == 1 for n in unique_per_case.values())
    return {
        "runs_per_case": _DETERMINISM_RUNS,
        "cases": len(cases),
        "total_reviews": _DETERMINISM_RUNS * len(cases),
        "unique_digests_per_case": unique_per_case,
        "max_unique_digests": max(unique_per_case.values()),
        "all_deterministic": stable,
    }


def _per_class_detection(
    cases: list[GoldenCase], verdicts: dict[str, ReviewVerdict]
) -> dict[str, dict[str, object]]:
    """Detection rate per planted Panko class: blocked / planted, with a Wilson CI."""
    planted: dict[str, int] = defaultdict(int)
    blocked: dict[str, int] = defaultdict(int)
    right_check: dict[str, int] = defaultdict(int)
    for case in cases:
        if case.is_control or case.planted_class is None:
            continue
        cls = case.planted_class.value
        planted[cls] += 1
        verdict = verdicts[case.case_id]
        if not verdict.passed:  # blocked == caught
            blocked[cls] += 1
        # Confirm the RIGHT check raised the RIGHT class (not an incidental block).
        if any(
            f.check_id == case.planted_check and f.defect_class == case.planted_class
            for f in verdict.findings
        ):
            right_check[cls] += 1
    out: dict[str, dict[str, object]] = {}
    for cls in sorted(planted):
        lo, hi = _wilson_interval(blocked[cls], planted[cls])
        out[cls] = {
            "planted": planted[cls],
            "blocked": blocked[cls],
            "detected_by_correct_check": right_check[cls],
            "detection_rate": blocked[cls] / planted[cls],
            "wilson95_low": lo,
            "wilson95_high": hi,
        }
    return out


def _headline_rates(
    cases: list[GoldenCase], verdicts: dict[str, ReviewVerdict]
) -> dict[str, object]:
    """Escape rate on planted defects and false-positive rate on controls."""
    planted = [c for c in cases if not c.is_control]
    controls = [c for c in cases if c.is_control]
    escaped = sum(1 for c in planted if verdicts[c.case_id].passed)
    false_pos = sum(1 for c in controls if not verdicts[c.case_id].passed)
    esc_lo, esc_hi = _wilson_interval(escaped, len(planted))
    fp_lo, fp_hi = _wilson_interval(false_pos, len(controls))
    return {
        "planted_total": len(planted),
        "controls_total": len(controls),
        "escapes": escaped,
        "escape_rate": escaped / len(planted) if planted else 0.0,
        "escape_rate_wilson95": [esc_lo, esc_hi],
        "false_positives": false_pos,
        "false_positive_rate": false_pos / len(controls) if controls else 0.0,
        "false_positive_rate_wilson95": [fp_lo, fp_hi],
        # The motivating baseline: un-reviewed human spreadsheets carry errors in
        # ~86% of cases while authors self-estimate ~18% (Panko; B16 SYNTHESIS A.1).
        "unreviewed_human_error_baseline": 0.86,
        "human_self_estimated_error": 0.18,
    }


def _write_per_case_csv(
    cases: list[GoldenCase], verdicts: dict[str, ReviewVerdict], path: Path
) -> None:
    """One row per case: label, verdict, and which checks/classes fired."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "case_id",
                "kind",
                "is_control",
                "planted_class",
                "planted_check",
                "verdict_passed",
                "blocking_findings",
                "fired_checks",
                "outcome",
            ]
        )
        for case in cases:
            verdict = verdicts[case.case_id]
            fired = sorted({f.check_id.value for f in verdict.findings})
            if case.is_control:
                outcome = "true_pass" if verdict.passed else "FALSE_POSITIVE"
            else:
                outcome = "ESCAPE" if verdict.passed else "caught"
            writer.writerow(
                [
                    case.case_id,
                    case.artifact.kind.value,
                    case.is_control,
                    case.planted_class.value if case.planted_class else "",
                    case.planted_check.value if case.planted_check else "",
                    verdict.passed,
                    len(verdict.blocking_findings),
                    "|".join(fired),
                    outcome,
                ]
            )


def main() -> None:
    """Build the corpus, run the gate, compute every number, and persist it."""
    _MEASURED_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="output_review_golden_") as tmp:
        cases = build_corpus(Path(tmp))
        verdicts = _review_all(cases)
        metrics = {
            "corpus_size": len(cases),
            "checks_in_floor": 7,
            "headline": _headline_rates(cases, verdicts),
            "detection_by_panko_class": _per_class_detection(cases, verdicts),
            "determinism": _measure_determinism(cases),
            "fixed_clock": _FIXED_CLOCK.isoformat(),
            "note": (
                "EUREKA (wrong domain model) is intentionally absent from the "
                "must-block set: it is the sole defect class the deterministic floor "
                "provably cannot reach and is routed to the advisory model layer."
            ),
        }
        (_MEASURED_DIR / "efficacy_metrics.json").write_text(
            json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
        )
        _write_per_case_csv(cases, verdicts, _MEASURED_DIR / "per_case.csv")

    head = metrics["headline"]
    det = metrics["determinism"]
    print(f"corpus: {metrics['corpus_size']} cases")
    print(f"escapes: {head['escapes']}/{head['planted_total']}  "
          f"(escape rate {head['escape_rate']:.3f})")
    print(f"false positives: {head['false_positives']}/{head['controls_total']}  "
          f"(rate {head['false_positive_rate']:.3f})")
    print(f"deterministic: {det['all_deterministic']} "
          f"({det['total_reviews']} reviews, max unique digests "
          f"{det['max_unique_digests']})")
    for cls, row in metrics["detection_by_panko_class"].items():
        print(f"  {cls}: detection {row['detection_rate']:.3f} "
              f"({row['blocked']}/{row['planted']})")


if __name__ == "__main__":
    main()
