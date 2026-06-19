"""Teeth-tests for the ACCOUNTING_IDENTITY check — A = L + E, exact to the unit.

These prove the check BLOCKS any balance sheet that fails ``assets == liabilities +
equity`` by even a sub-unit amount, PASSES only when every period balances exactly,
refuses fail-closed when a financial model carries no balance-sheet facts, and
declines (empty tuple) for kinds it does not own — deterministically (CLAUDE.md
§3.6, §3.11, §5.6). Every test would FAIL if the check were wrong; none is
tautological. Boundary cases pin the on/just-over/just-under edge with
``Decimal("0.01")``; property and metamorphic tests prove generality, not
scenario-fit; the determinism test pins byte-identical output across repeats.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.output_review.accounting_identity_check import AccountingIdentityCheck
from autofirm.output_review.review_check_protocol import ReviewCheck
from autofirm.output_review.review_finding_and_severity_contracts import (
    CHECK_DEFECT_CLASSES,
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
)
from autofirm.output_review.reviewable_artifact_contract import (
    ArtifactKind,
    ReviewableArtifact,
)
from autofirm.output_review.reviewable_artifact_facts import (
    BalanceSheetFigures,
    BalanceSheetPeriod,
)

_SYNTHETIC_PATH = Path("synthetic") / "model.xlsx"  # never read; checks are by-value


def _period(label: str, assets: Decimal, liabilities: Decimal, equity: Decimal) -> (
    BalanceSheetPeriod
):
    """A single synthetic balance-sheet period (all figures exact Decimal)."""
    return BalanceSheetPeriod(
        period=label, assets=assets, liabilities=liabilities, equity=equity
    )


def _model(*periods: BalanceSheetPeriod, ref: str = "art-fin-1") -> ReviewableArtifact:
    """A FINANCIAL_MODEL artifact carrying the given balance-sheet periods."""
    return ReviewableArtifact(
        artifact_ref=ref,
        kind=ArtifactKind.FINANCIAL_MODEL,
        path=_SYNTHETIC_PATH,
        balance_sheet=BalanceSheetFigures(periods=tuple(periods)),
    )


_CHECK = AccountingIdentityCheck()


# ---- Protocol + identity -------------------------------------------------------


def test_satisfies_review_check_protocol() -> None:
    assert isinstance(AccountingIdentityCheck(), ReviewCheck)


def test_id_is_accounting_identity() -> None:
    assert _CHECK.id is ReviewCheckId.ACCOUNTING_IDENTITY


def test_defect_class_is_registered_for_this_check() -> None:
    # Guards against the check ever emitting a class it does not own (would let a
    # finding carry an unclassifiable defect — the omission defence).
    assert DefectClass.PURE_LOGIC in CHECK_DEFECT_CLASSES[ReviewCheckId.ACCOUNTING_IDENTITY]


# ---- boundary-exact: on / just-over / just-under -------------------------------


def test_exact_balance_passes() -> None:
    findings = _CHECK.run(
        _model(_period("FY24", Decimal("100.00"), Decimal("60.00"), Decimal("40.00")))
    )
    assert findings == ()


def test_off_by_one_cent_over_fails() -> None:
    # just-over: assets exceed L+E by 0.01 — MUST block (no tolerance).
    findings = _CHECK.run(
        _model(_period("FY24", Decimal("100.01"), Decimal("60.00"), Decimal("40.00")))
    )
    assert len(findings) == 1
    assert findings[0].severity is CheckSeverity.BLOCKING


def test_off_by_one_cent_under_fails() -> None:
    # just-under: assets short of L+E by 0.01 — MUST block.
    findings = _CHECK.run(
        _model(_period("FY24", Decimal("99.99"), Decimal("60.00"), Decimal("40.00")))
    )
    assert len(findings) == 1
    assert findings[0].severity is CheckSeverity.BLOCKING


def test_finding_carries_exact_expected_and_actual() -> None:
    findings = _CHECK.run(
        _model(_period("FY24", Decimal("100"), Decimal("60"), Decimal("39")))
    )
    (finding,) = findings
    assert finding.check_id is ReviewCheckId.ACCOUNTING_IDENTITY
    assert finding.defect_class is DefectClass.PURE_LOGIC
    assert finding.locator == "FY24"
    assert finding.expected == "A=100"
    assert finding.actual == "L+E=99"


def test_trailing_zero_difference_does_not_falsely_balance() -> None:
    # Decimal("100.0") == Decimal("100") numerically, so a model where assets differ
    # only by representation must still be judged on VALUE — here it truly balances.
    findings = _CHECK.run(
        _model(_period("FY24", Decimal("100.0"), Decimal("100"), Decimal("0")))
    )
    assert findings == ()


# ---- degenerate / nooks-and-crannies -------------------------------------------


def test_all_zero_period_passes() -> None:
    findings = _CHECK.run(
        _model(_period("FY24", Decimal("0"), Decimal("0"), Decimal("0")))
    )
    assert findings == ()


def test_negative_equity_but_balanced_passes() -> None:
    # A distressed firm: equity negative, yet A = L + E still holds exactly.
    findings = _CHECK.run(
        _model(_period("FY24", Decimal("50"), Decimal("130"), Decimal("-80")))
    )
    assert findings == ()


def test_multi_period_exactly_one_bad_yields_one_finding_at_that_period() -> None:
    findings = _CHECK.run(
        _model(
            _period("FY22", Decimal("10"), Decimal("4"), Decimal("6")),  # balanced
            _period("FY23", Decimal("21"), Decimal("10"), Decimal("10")),  # bad: 21!=20
            _period("FY24", Decimal("30"), Decimal("0"), Decimal("30")),  # balanced
        )
    )
    assert len(findings) == 1
    assert findings[0].locator == "FY23"


def test_findings_preserve_given_period_order() -> None:
    findings = _CHECK.run(
        _model(
            _period("FY22", Decimal("1"), Decimal("0"), Decimal("0")),  # bad
            _period("FY23", Decimal("5"), Decimal("2"), Decimal("2")),  # bad
        )
    )
    assert tuple(f.locator for f in findings) == ("FY22", "FY23")


# ---- non-applicable kind + fail-closed missing facts ---------------------------


@pytest.mark.parametrize(
    "kind", [ArtifactKind.SLIDE_DECK, ArtifactKind.BUSINESS_DOCUMENT]
)
def test_non_financial_kind_is_not_applicable(kind: ArtifactKind) -> None:
    artifact = ReviewableArtifact(
        artifact_ref="art-deck-1", kind=kind, path=_SYNTHETIC_PATH
    )
    assert _CHECK.run(artifact) == ()


def test_financial_model_without_balance_sheet_blocks_fail_closed() -> None:
    artifact = ReviewableArtifact(
        artifact_ref="art-no-facts",
        kind=ArtifactKind.FINANCIAL_MODEL,
        path=_SYNTHETIC_PATH,
        balance_sheet=None,
    )
    findings = _CHECK.run(artifact)
    assert len(findings) == 1
    only = findings[0]
    assert only.severity is CheckSeverity.BLOCKING
    assert only.defect_class is DefectClass.PURE_LOGIC
    assert only.locator == "art-no-facts"  # locator is the artifact ref
    assert "cannot verify" in only.message


# ---- determinism ---------------------------------------------------------------


def test_run_is_byte_identical_across_repeats() -> None:
    artifact = _model(
        _period("FY23", Decimal("21"), Decimal("10"), Decimal("10")),
        _period("FY24", Decimal("30"), Decimal("0"), Decimal("30")),
    )
    runs = [_CHECK.run(artifact) for _ in range(8)]
    first = runs[0]
    for other in runs[1:]:
        assert other == first
        assert [f.model_dump() for f in other] == [f.model_dump() for f in first]


# ---- PROPERTY: balanced always passes, any nonzero delta always fails ----------

_FIGURE = st.decimals(
    min_value=Decimal("-1e6"),
    max_value=Decimal("1e6"),
    allow_nan=False,
    allow_infinity=False,
    places=2,
)
_NONZERO_DELTA = _FIGURE.filter(lambda d: d != Decimal(0))


@settings(max_examples=400)
@given(liabilities=_FIGURE, equity=_FIGURE)
def test_property_assets_equal_l_plus_e_always_passes(
    liabilities: Decimal, equity: Decimal
) -> None:
    """For ANY L, E: setting assets := L + E yields an exactly balanced sheet."""
    findings = _CHECK.run(
        _model(_period("FY", liabilities + equity, liabilities, equity))
    )
    assert findings == ()


@settings(max_examples=400)
@given(liabilities=_FIGURE, equity=_FIGURE, delta=_NONZERO_DELTA)
def test_property_any_nonzero_delta_always_fails(
    liabilities: Decimal, equity: Decimal, delta: Decimal
) -> None:
    """For ANY L, E and ANY nonzero delta: assets := L + E + delta must block."""
    findings = _CHECK.run(
        _model(_period("FY", liabilities + equity + delta, liabilities, equity))
    )
    assert len(findings) == 1
    assert findings[0].severity is CheckSeverity.BLOCKING


# ---- METAMORPHIC: scaling preserves the verdict --------------------------------

_INT_FIGURE = st.integers(min_value=-100_000, max_value=100_000)
_NONZERO_FACTOR = st.integers(min_value=-1000, max_value=1000).filter(lambda n: n != 0)


@settings(max_examples=300)
@given(liabilities=_INT_FIGURE, equity=_INT_FIGURE, factor=_NONZERO_FACTOR)
def test_metamorphic_scaling_a_balanced_sheet_stays_balanced(
    liabilities: int, equity: int, factor: int
) -> None:
    """Scaling every figure of a balanced sheet by a constant preserves PASS."""
    f = Decimal(factor)
    liab, eq = Decimal(liabilities) * f, Decimal(equity) * f
    assets = (Decimal(liabilities) + Decimal(equity)) * f  # scaled balanced assets
    assert _CHECK.run(_model(_period("FY", assets, liab, eq))) == ()


@settings(max_examples=300)
@given(
    liabilities=_INT_FIGURE,
    equity=_INT_FIGURE,
    delta=st.integers(min_value=-50_000, max_value=50_000).filter(lambda n: n != 0),
    factor=_NONZERO_FACTOR,
)
def test_metamorphic_scaling_an_unbalanced_sheet_stays_unbalanced(
    liabilities: int, equity: int, delta: int, factor: int
) -> None:
    """Scaling every figure of an unbalanced sheet by a constant preserves FAIL."""
    f = Decimal(factor)
    liab, eq = Decimal(liabilities) * f, Decimal(equity) * f
    assets = (Decimal(liabilities) + Decimal(equity) + Decimal(delta)) * f
    findings = _CHECK.run(_model(_period("FY", assets, liab, eq)))
    assert len(findings) == 1
    assert findings[0].severity is CheckSeverity.BLOCKING
