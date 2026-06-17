"""Shared fixtures for the end-to-end validation suite.

Every fixture roots the validation under the test's ``tmp_path`` so NOTHING is
ever written into the real on-disk ``.autofirm/`` (CLAUDE.md §3.12) and the whole
corpus is auto-deleted by pytest after each test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autofirm.e2e.end_to_end_validation_harness import EndToEndValidationHarness
from autofirm.e2e.public_company_scenarios import (
    PublicCompanyScenario,
    public_company_scenarios,
)
from autofirm.e2e.scenario_result_contract import ValidationSummary


@pytest.fixture
def corpus_dir(tmp_path: Path) -> Path:
    """A per-test deletable corpus directory under pytest's tmp_path (never real .autofirm)."""
    root = tmp_path / "validation-corpus"
    root.mkdir()
    return root


@pytest.fixture
def harness(corpus_dir: Path) -> EndToEndValidationHarness:
    """A harness bound to the per-test corpus over the full public-data scenario set."""
    return EndToEndValidationHarness(corpus_dir)


@pytest.fixture
def summary(harness: EndToEndValidationHarness) -> ValidationSummary:
    """The result of running the full build+operate validation once (reused across asserts)."""
    return harness.run()


@pytest.fixture
def scenarios() -> tuple[PublicCompanyScenario, ...]:
    """The frozen public-data scenario corpus."""
    return public_company_scenarios()
