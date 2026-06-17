"""Structured, machine-readable results the showcase consumes.

Every scenario emits one :class:`ScenarioResult` (what was built, which features
ran, pass/fail per feature, the key numbers each feature produced). The harness
collects them into a :class:`ValidationSummary` carrying corpus-wide counts and a
per-feature pass matrix. Both are plain pydantic models so the ``evidence/``
showcase can load them as JSON without importing any runtime engine.

Why a closed feature vocabulary
-------------------------------
:class:`FeatureName` is a closed set: a scenario can only report a feature the
platform actually has, so the pass matrix can never silently grow a typo'd column
and the showcase always renders the same fixed grid of capabilities.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class FeatureStatus(StrEnum):
    """The outcome of one exercised platform feature within a scenario."""

    PASSED = "passed"  # the feature ran and its real output was asserted correct
    FAILED = "failed"  # the feature ran but produced a wrong/unsensible result


class FeatureName(StrEnum):
    """Closed set of the platform capabilities the validation exercises.

    Mirrors the platform packages so the per-feature pass matrix is a fixed,
    well-known grid. Build-phase capabilities and operate-phase capabilities both
    appear here; the phase is recorded on each :class:`FeatureCheck`.
    """

    ORG_FOUNDED = "org_founded"  # org engine stood the company up
    GAP_AUTO_CREATE_HIRE = "gap_auto_create_hire"  # gap -> auto-create + hire a role
    COMMS_WIRED = "comms_wired"  # inter-agent message bus delivered a message
    DOCUMENTS_FILED = "documents_filed"  # document store catalogued a deliverable
    FINANCE_STATEMENTS = "finance_statements"  # 3 statements articulated + tie
    FINANCE_VALUATION = "finance_valuation"  # DCF / valuation computed
    PRICING_DECISION = "pricing_decision"  # explainable price recommendation
    RUNWAY_DECISION = "runway_decision"  # explainable runway scenario
    MARKET_INTEL_SWEEP = "market_intel_sweep"  # sense the market -> structured insights
    GREEN_LIGHT_GATE = "green_light_gate"  # go / no-go verdict with rationale
    FRONT_DOOR_ROUTING = "front_door_routing"  # human question routed to the right team
    ARTIFACT_GENERATED = "artifact_generated"  # investor-ready artifact written
    HEARTBEAT_TICK = "heartbeat_tick"  # a recurring beat fired deterministically
    FLOW_HANDOFF = "flow_handoff"  # a work item moved through the org
    FAIL_CLOSED_GUARD = "fail_closed_guard"  # a bad input was refused (edge case)


class FeatureCheck(BaseModel):
    """One exercised feature's verdict plus the key numbers it produced.

    ``evidence`` holds the load-bearing real-shaped outputs the assertion checked
    (e.g. the net income, the recommended price, the routed role) so the showcase
    can display *what* the platform produced, not merely that it passed.
    """

    model_config = ConfigDict(frozen=True)

    feature: FeatureName
    phase: str  # "build" or "operate"
    status: FeatureStatus
    detail: str  # one-line human-readable summary of what was verified
    evidence: dict[str, str] = Field(default_factory=dict)

    def passed(self) -> bool:
        """True iff this feature's real output was asserted correct."""
        return self.status is FeatureStatus.PASSED


class ScenarioResult(BaseModel):
    """The full structured outcome of building + operating one company.

    Written into the company's own isolated workspace AND collected into the
    corpus-wide :class:`ValidationSummary`.
    """

    model_config = ConfigDict(frozen=True)

    company_slug: str  # slug-safe id of the company (also its workspace folder)
    company_name: str  # public, human-readable company name
    industry: str  # the diverse industry this scenario covers
    data_source: str  # always public — the provenance label ("public-data only")
    workspace_root: str  # the isolated, deletable .autofirm root for this company
    checks: tuple[FeatureCheck, ...]

    def all_passed(self) -> bool:
        """True iff every exercised feature passed (the scenario is GREEN)."""
        return all(check.passed() for check in self.checks)

    def features_passed(self) -> int:
        """Count of features whose real output was asserted correct."""
        return sum(1 for check in self.checks if check.passed())


class ValidationSummary(BaseModel):
    """Corpus-wide rollup: counts + a per-feature pass matrix for the showcase.

    ``feature_matrix`` maps each exercised :class:`FeatureName` to the number of
    scenarios in which it passed, giving the showcase a fixed capability grid.
    """

    model_config = ConfigDict(frozen=True)

    scenarios: tuple[ScenarioResult, ...]

    def total_scenarios(self) -> int:
        """How many companies were built + operated."""
        return len(self.scenarios)

    def scenarios_all_green(self) -> int:
        """How many companies passed every exercised feature."""
        return sum(1 for scenario in self.scenarios if scenario.all_passed())

    def total_checks(self) -> int:
        """Total feature checks across the whole corpus."""
        return sum(len(scenario.checks) for scenario in self.scenarios)

    def checks_passed(self) -> int:
        """Total feature checks that passed across the whole corpus."""
        return sum(scenario.features_passed() for scenario in self.scenarios)

    def feature_matrix(self) -> dict[str, int]:
        """Per-feature pass count across all scenarios (the showcase grid)."""
        matrix: dict[str, int] = {}
        for scenario in self.scenarios:
            for check in scenario.checks:
                key = check.feature.value
                matrix[key] = matrix.get(key, 0) + (1 if check.passed() else 0)
        return matrix
