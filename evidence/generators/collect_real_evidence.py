"""Collect ALL real evidence into one JSON the showcase generators consume.

This is the single source of truth for every number in the showcase: it reads the
real coverage report (``evidence/_raw/coverage.json``, written by ``pytest --cov``)
and runs the real end-to-end validation harness over the four public-data
companies. NOTHING here is fabricated — every figure traces to a real run.

Analysis-only (CLAUDE.md §3.10): imports the runtime ``autofirm.e2e`` package to
*read* its real output, but is itself part of the ``evidence/`` showcase and is
never imported by any runtime package.
"""

from __future__ import annotations

import json
import tempfile
from collections import defaultdict
from pathlib import Path

from autofirm.e2e.end_to_end_validation_harness import run_all_scenarios

_HERE = Path(__file__).resolve().parent
_EVIDENCE = _HERE.parent
_RAW = _EVIDENCE / "_raw"
_COVERAGE_JSON = _RAW / "coverage.json"
_TEST_COUNT_FILE = _RAW / "test_count.txt"
_OUT = _RAW / "evidence_data.json"

# Map a coverage file path to the top-level platform package it belongs to, so
# per-file coverage rolls up into the 18 platform components the showcase grids.
_PACKAGE_SEGMENT = "autofirm"


def _package_of(file_path: str) -> str | None:
    """Return the top-level ``autofirm`` subpackage for a coverage file path."""
    parts = Path(file_path).as_posix().split("/")
    if _PACKAGE_SEGMENT not in parts:
        return None
    idx = parts.index(_PACKAGE_SEGMENT)
    # The package is the segment right after ``autofirm`` (a dir); a file directly
    # under autofirm/ (e.g. __init__) is attributed to the root package.
    if idx + 2 >= len(parts):
        return _PACKAGE_SEGMENT
    return parts[idx + 1]


def _per_package_coverage() -> dict[str, dict[str, float]]:
    """Roll the real per-file coverage report up into per-package line+branch %."""
    report = json.loads(_COVERAGE_JSON.read_text(encoding="utf-8"))
    statements: dict[str, int] = defaultdict(int)
    covered: dict[str, int] = defaultdict(int)
    branches: dict[str, int] = defaultdict(int)
    branches_covered: dict[str, int] = defaultdict(int)
    for file_path, data in report["files"].items():
        pkg = _package_of(file_path)
        if pkg is None:
            continue
        summary = data["summary"]
        statements[pkg] += summary["num_statements"]
        covered[pkg] += summary["covered_lines"]
        branches[pkg] += summary["num_branches"]
        branches_covered[pkg] += summary["covered_branches"]
    out: dict[str, dict[str, float]] = {}
    for pkg in sorted(statements):
        line_pct = 100.0 * covered[pkg] / statements[pkg] if statements[pkg] else 100.0
        br_pct = (
            100.0 * branches_covered[pkg] / branches[pkg] if branches[pkg] else 100.0
        )
        out[pkg] = {
            "line_pct": round(line_pct, 2),
            "branch_pct": round(br_pct, 2),
            "statements": statements[pkg],
        }
    return out


def _totals() -> dict[str, float]:
    """Return the real corpus-wide coverage totals from the coverage report."""
    totals = json.loads(_COVERAGE_JSON.read_text(encoding="utf-8"))["totals"]
    return {
        "line_pct": round(totals["percent_covered"], 2),
        "statements": totals["num_statements"],
        "branches": totals["num_branches"],
    }


def _e2e_evidence() -> dict[str, object]:
    """Run the real validation harness and capture the corpus-wide evidence."""
    with tempfile.TemporaryDirectory() as tmp:
        summary = run_all_scenarios(Path(tmp))
        companies = []
        for scenario in summary.scenarios:
            fin = {
                check.feature.value: dict(check.evidence)
                for check in scenario.checks
                if check.evidence
            }
            companies.append(
                {
                    "slug": scenario.company_slug,
                    "name": scenario.company_name,
                    "industry": scenario.industry,
                    "features_passed": scenario.features_passed(),
                    "features_total": len(scenario.checks),
                    "all_green": scenario.all_passed(),
                    "evidence": fin,
                }
            )
        # Per (company, feature) pass grid for the heatmap: 1 = passed.
        feature_order = [check.feature.value for check in summary.scenarios[0].checks]
        grid = {
            scenario.company_slug: {
                check.feature.value: 1 if check.passed() else 0
                for check in scenario.checks
            }
            for scenario in summary.scenarios
        }
        return {
            "total_scenarios": summary.total_scenarios(),
            "scenarios_all_green": summary.scenarios_all_green(),
            "total_checks": summary.total_checks(),
            "checks_passed": summary.checks_passed(),
            "feature_order": feature_order,
            "feature_matrix": summary.feature_matrix(),
            "grid": grid,
            "companies": companies,
        }


def _real_test_count() -> int:
    """Read the real collected-test count pytest wrote to ``test_count.txt``.

    The file holds pytest's own ``N tests collected`` line, so the headline test
    number traces to a real suite run rather than a hand-typed constant.
    """
    text = _TEST_COUNT_FILE.read_text(encoding="utf-8")
    for token in text.split():
        if token.isdigit():
            return int(token)
    raise ValueError(f"no test count found in {_TEST_COUNT_FILE}: {text!r}")


def collect(test_count: int) -> dict[str, object]:
    """Assemble the full evidence payload (test count is passed from the suite run)."""
    return {
        "test_count": test_count,
        "coverage_totals": _totals(),
        "per_package_coverage": _per_package_coverage(),
        "e2e": _e2e_evidence(),
    }


if __name__ == "__main__":
    payload = collect(test_count=_real_test_count())
    _OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {_OUT}")
    print(f"  tests={payload['test_count']}")
    cov = payload["coverage_totals"]
    print(f"  coverage line%={cov['line_pct']} statements={cov['statements']}")
    e2e = payload["e2e"]
    print(
        f"  e2e companies={e2e['total_scenarios']} "
        f"checks={e2e['checks_passed']}/{e2e['total_checks']}"
    )
