"""The end-to-end validation harness: build + operate every company, emit a summary.

This is the top of the validation: for each public-data scenario it creates an
isolated, deletable workspace, BUILDS the company (org/gap/comms/docs), OPERATES
it (every major feature), writes the structured :class:`ScenarioResult` into that
company's own workspace as JSON, and collects all results into a corpus-wide
:class:`ValidationSummary` (counts + a per-feature pass matrix) that the
``evidence/`` showcase consumes.

Isolation + deletability (CLAUDE.md §3.12)
------------------------------------------
Every company's artifacts, filed documents, and result file live under its own
``.autofirm/`` root inside the corpus directory; :meth:`EndToEndValidationHarness
.teardown` deletes each workspace and asserts it is gone, proving the whole corpus
is removable without touching the platform.
"""

from __future__ import annotations

from pathlib import Path

from autofirm.e2e.company_build_flow import build_company
from autofirm.e2e.company_operate_flow import operate_company
from autofirm.e2e.isolated_company_workspace import (
    IsolatedCompanyWorkspace,
    create_isolated_company_workspace,
)
from autofirm.e2e.public_company_scenarios import (
    PublicCompanyScenario,
    public_company_scenarios,
)
from autofirm.e2e.scenario_result_contract import ScenarioResult, ValidationSummary

# The label every result carries, asserting the validation used PUBLIC data only.
PUBLIC_DATA_LABEL = "public-data only"
_RESULT_FILENAME = "scenario-result.json"


class EndToEndValidationHarness:
    """Runs the build+operate validation over a scenario corpus in isolated workspaces.

    Args:
        corpus_dir: The deletable parent directory holding every company's
            workspace (a test's ``tmp_path``). Nothing is ever written outside it.
        scenarios: The public-data scenarios to validate (defaults to the full
            frozen corpus).
    """

    def __init__(
        self,
        corpus_dir: Path,
        scenarios: tuple[PublicCompanyScenario, ...] | None = None,
    ) -> None:
        """Bind the harness to its corpus dir and scenario set; no work runs yet."""
        self._corpus_dir = corpus_dir
        self._scenarios = scenarios if scenarios is not None else public_company_scenarios()
        self._workspaces: list[IsolatedCompanyWorkspace] = []

    def run(self) -> ValidationSummary:
        """Build + operate every scenario; write per-company results; return the summary."""
        results: list[ScenarioResult] = []
        for scenario in self._scenarios:
            results.append(self._run_one(scenario))
        return ValidationSummary(scenarios=tuple(results))

    def _run_one(self, scenario: PublicCompanyScenario) -> ScenarioResult:
        """Build + operate one company in its own isolated workspace; persist the result."""
        workspace = create_isolated_company_workspace(
            company_slug=scenario.slug, corpus_dir=self._corpus_dir
        )
        self._workspaces.append(workspace)

        built = build_company(scenario, workspace)
        operate_checks = operate_company(scenario, built.org, built.librarian, workspace)

        result = ScenarioResult(
            company_slug=scenario.slug,
            company_name=scenario.name,
            industry=scenario.industry,
            data_source=PUBLIC_DATA_LABEL,  # provenance: public data only
            workspace_root=str(workspace.root_dir),
            checks=built.checks + operate_checks,
        )
        # Persist the machine-readable result INSIDE the company's own isolated
        # workspace, so each company carries its own showcase artifact and the
        # corpus stays self-contained + deletable.
        result_path = workspace.root_dir / _RESULT_FILENAME
        result_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        return result

    def teardown(self) -> None:
        """Delete every company workspace and assert each is gone (deletability proof)."""
        while self._workspaces:
            self._workspaces.pop().teardown()


def run_all_scenarios(corpus_dir: Path) -> ValidationSummary:
    """Convenience: run the full public-data corpus under ``corpus_dir`` and return the summary.

    Does NOT tear down — the caller owns the corpus dir (a test's ``tmp_path``,
    auto-removed by pytest) so the written per-company result files remain
    inspectable for the showcase before cleanup.
    """
    return EndToEndValidationHarness(corpus_dir).run()
