"""The marquee gate: every diverse company BUILDS and OPERATES with every feature green.

These tests are the teeth of the final validation (CLAUDE.md §3.12): they assert
that across four genuinely different industries the WHOLE platform stands each
company up and runs every major feature with its REAL output asserted correct.
The per-(company, feature) parametrization means a single weak feature on a
single company fails its own named test — no aggregate hides a regression.
"""

from __future__ import annotations

import pytest

from autofirm.e2e.public_company_scenarios import (
    PublicCompanyScenario,
    public_company_scenarios,
)
from autofirm.e2e.scenario_result_contract import (
    FeatureName,
    ScenarioResult,
    ValidationSummary,
)

# Every capability the validation MUST exercise for each company — the full grid.
_EXPECTED_FEATURES = frozenset(FeatureName)

_SCENARIOS = public_company_scenarios()
_SCENARIO_IDS = [s.slug for s in _SCENARIOS]


def _result_for(summary: ValidationSummary, slug: str) -> ScenarioResult:
    return next(s for s in summary.scenarios if s.company_slug == slug)


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_SCENARIO_IDS)
def test_every_company_is_all_green(
    summary: ValidationSummary, scenario: PublicCompanyScenario
) -> None:
    """Each diverse company builds + operates with EVERY exercised feature passing."""
    result = _result_for(summary, scenario.slug)
    failed = [c.feature.value for c in result.checks if not c.passed()]
    assert failed == [], f"{scenario.slug} had failing features: {failed}"
    assert result.all_passed()


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=_SCENARIO_IDS)
def test_every_feature_is_exercised_per_company(
    summary: ValidationSummary, scenario: PublicCompanyScenario
) -> None:
    """No capability is silently skipped: every FeatureName is checked for each company.

    A harness that quietly stopped exercising a feature (the classic false-green)
    is caught here because the set of checked features must equal the full grid.
    """
    result = _result_for(summary, scenario.slug)
    exercised = {check.feature for check in result.checks}
    assert exercised == _EXPECTED_FEATURES


def test_corpus_is_diverse_across_industries(summary: ValidationSummary) -> None:
    """The corpus spans 3+ DISTINCT industries (generalisation, not one business model)."""
    industries = {s.industry for s in summary.scenarios}
    assert len(summary.scenarios) >= 3
    assert len(industries) == len(summary.scenarios)  # every industry distinct


def test_feature_matrix_is_full_green(summary: ValidationSummary) -> None:
    """The showcase pass matrix shows every feature passing in every scenario."""
    matrix = summary.feature_matrix()
    n = summary.total_scenarios()
    # Every known feature passed in all n scenarios -> the grid is fully green.
    assert set(matrix) == {f.value for f in FeatureName}
    assert all(passes == n for passes in matrix.values())
    assert summary.checks_passed() == summary.total_checks()
    assert summary.scenarios_all_green() == n


_FEATURES_SORTED = sorted(FeatureName, key=lambda f: f.value)


@pytest.mark.parametrize("feature", _FEATURES_SORTED, ids=[f.value for f in _FEATURES_SORTED])
def test_each_feature_passes_in_every_scenario(
    summary: ValidationSummary, feature: FeatureName
) -> None:
    """Per-feature gate: this capability works for ALL companies (named per feature)."""
    passing = summary.feature_matrix()[feature.value]
    assert passing == summary.total_scenarios()
