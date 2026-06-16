"""Adversarial validation tests for the FAST financial-model spec contract.

Proves the spec is fail-closed (CLAUDE.md §5.6): every malformed model is refused
with ``ArtifactSpecError`` at construction, before any builder runs. These tests
have teeth — each targets a distinct structural defect a real model could carry.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.artifacts.artifact_spec_validation_errors import ArtifactSpecError
from autofirm.artifacts.financial_model_spec import (
    CalculationRow,
    FinancialModelSpec,
    InputDriver,
    _referenced_keys,
)


def _driver(key: str = "revenue", n: int = 2) -> InputDriver:
    return InputDriver(key, key.title(), tuple(Decimal(i) for i in range(n)))


def test_valid_spec_constructs() -> None:
    spec = FinancialModelSpec(
        title="M",
        periods=("FY24", "FY25"),
        drivers=(_driver("revenue"), _driver("cogs")),
        calculations=(CalculationRow("gp", "Gross profit", "={revenue} - {cogs}"),),
        outputs=("gp",),
    )
    assert spec.calculations[0].key == "gp"


@pytest.mark.parametrize("title", ["", "   ", "\t\n"])
def test_blank_title_refused(title: str) -> None:
    with pytest.raises(ArtifactSpecError, match="title"):
        FinancialModelSpec(title=title, periods=("FY24",), drivers=(_driver("r", 1),))


def test_no_periods_refused() -> None:
    with pytest.raises(ArtifactSpecError, match="period"):
        FinancialModelSpec(title="M", periods=(), drivers=(_driver("r", 0),))


def test_no_drivers_refused() -> None:
    with pytest.raises(ArtifactSpecError, match="driver"):
        FinancialModelSpec(title="M", periods=("FY24",), drivers=())


def test_driver_value_vector_too_short_refused() -> None:
    # A short vector would silently blank cells -> a wrong model. Must be refused.
    with pytest.raises(ArtifactSpecError, match="expected 3"):
        FinancialModelSpec(
            title="M",
            periods=("a", "b", "c"),
            drivers=(InputDriver("r", "R", (Decimal(1), Decimal(2))),),
        )


def test_driver_value_vector_too_long_refused() -> None:
    with pytest.raises(ArtifactSpecError, match="expected 1"):
        FinancialModelSpec(
            title="M",
            periods=("a",),
            drivers=(InputDriver("r", "R", (Decimal(1), Decimal(2))),),
        )


@pytest.mark.parametrize("bad_key", ["1revenue", "rev-enue", "rev enue", "", "_rev", "rév"])
def test_invalid_driver_key_refused(bad_key: str) -> None:
    # Keys become formula/label tokens; a non-identifier could inject a formula.
    with pytest.raises(ArtifactSpecError, match="must match"):
        FinancialModelSpec(
            title="M", periods=("a",), drivers=(InputDriver(bad_key, "L", (Decimal(1),)),)
        )


def test_duplicate_keys_refused() -> None:
    with pytest.raises(ArtifactSpecError, match="duplicate"):
        FinancialModelSpec(
            title="M", periods=("a",), drivers=(_driver("r", 1), _driver("r", 1))
        )


def test_calc_referencing_unknown_key_refused() -> None:
    with pytest.raises(ArtifactSpecError, match="unknown/forward"):
        FinancialModelSpec(
            title="M",
            periods=("a",),
            drivers=(_driver("r", 1),),
            calculations=(CalculationRow("c", "C", "={ghost}"),),
        )


def test_calc_forward_reference_refused() -> None:
    # ICAEW P15: a row may only reference already-defined keys (no forward refs).
    with pytest.raises(ArtifactSpecError, match="unknown/forward"):
        FinancialModelSpec(
            title="M",
            periods=("a",),
            drivers=(_driver("r", 1),),
            calculations=(
                CalculationRow("first", "First", "={later}"),
                CalculationRow("later", "Later", "={r}"),
            ),
        )


def test_calc_self_reference_refused() -> None:
    with pytest.raises(ArtifactSpecError, match="itself"):
        FinancialModelSpec(
            title="M",
            periods=("a",),
            drivers=(_driver("r", 1),),
            calculations=(CalculationRow("c", "C", "={c} + {r}"),),
        )


def test_calc_with_no_references_refused() -> None:
    # A "calculation" with no references is just an embedded constant (ICAEW P14).
    with pytest.raises(ArtifactSpecError, match="embedded constant"):
        FinancialModelSpec(
            title="M",
            periods=("a",),
            drivers=(_driver("r", 1),),
            calculations=(CalculationRow("c", "C", "=42"),),
        )


def test_unknown_output_key_refused() -> None:
    with pytest.raises(ArtifactSpecError, match="not a driver or calculation"):
        FinancialModelSpec(
            title="M", periods=("a",), drivers=(_driver("r", 1),), outputs=("ghost",)
        )


@pytest.mark.parametrize("label", ["", "  "])
def test_blank_driver_label_refused(label: str) -> None:
    with pytest.raises(ArtifactSpecError, match="non-empty label"):
        FinancialModelSpec(
            title="M", periods=("a",), drivers=(InputDriver("r", label, (Decimal(1),)),)
        )


@pytest.mark.parametrize("label", ["", "  "])
def test_blank_calculation_label_refused(label: str) -> None:
    with pytest.raises(ArtifactSpecError, match="non-empty label"):
        FinancialModelSpec(
            title="M",
            periods=("a",),
            drivers=(_driver("r", 1),),
            calculations=(CalculationRow("c", label, "={r}"),),
        )


def test_calculation_key_duplicating_driver_refused() -> None:
    # A calc key that collides with a driver key makes references ambiguous.
    with pytest.raises(ArtifactSpecError, match="duplicate"):
        FinancialModelSpec(
            title="M",
            periods=("a",),
            drivers=(_driver("r", 1),),
            calculations=(CalculationRow("r", "Dup", "={r}"),),
        )


def test_calculation_key_duplicating_earlier_calc_refused() -> None:
    with pytest.raises(ArtifactSpecError, match="duplicate"):
        FinancialModelSpec(
            title="M",
            periods=("a",),
            drivers=(_driver("r", 1),),
            calculations=(
                CalculationRow("c", "C1", "={r}"),
                CalculationRow("c", "C2", "={r}"),
            ),
        )


@pytest.mark.property
@given(template=st.text(min_size=0, max_size=40))
def test_referenced_keys_dedupes_and_preserves_order(template: str) -> None:
    refs = _referenced_keys(template)
    assert len(refs) == len(set(refs))  # no duplicates
    # Every returned key actually appears as a placeholder in the template.
    for ref in refs:
        assert "{" + ref + "}" in template


@pytest.mark.property
@given(
    keys=st.lists(
        st.from_regex(r"[A-Za-z][A-Za-z0-9_]{0,5}", fullmatch=True),
        min_size=1,
        max_size=4,
        unique=True,
    )
)
def test_referenced_keys_finds_all_distinct_placeholders(keys: list[str]) -> None:
    template = "=" + " + ".join("{" + k + "}" for k in keys)
    assert set(_referenced_keys(template)) == set(keys)
