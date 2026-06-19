"""Teeth-tests for the OutputReviewGate composition + fail-closed behaviour.

These prove the gate (CLAUDE.md §3.6, §3.11, §5.6): composes the seven floor checks
into ONE derived verdict; PASSES a clean artifact only when every check is silent;
BLOCKS a planted defect with the right check_id/locator; refuses an empty registry
(fail-closed — a no-check gate would vacuously pass everything); turns a RAISING check
into a BLOCKING finding without crashing or skipping the remaining checks; records an
omitted check's absence in ``checks_run`` (omission defence); is byte-identical across
repeats under an injected clock; preserves a deterministic (registry-then-per-check)
finding order; and NEVER manufactures a false pass (property — passed iff no blocking
finding). Every test would FAIL if the gate were wrong; none is tautological.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.output_review.default_output_review_gate_factory import (
    build_default_output_review_gate,
)
from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.output_review_gate import OutputReviewGate
from autofirm.output_review.review_check_protocol import CheckRegistry
from autofirm.output_review.review_finding_and_severity_contracts import (
    CHECK_DEFECT_CLASSES,
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
    ReviewFinding,
)
from autofirm.output_review.reviewable_artifact_contract import (
    ArtifactKind,
    ReviewableArtifact,
)
from autofirm.output_review.reviewable_artifact_facts import (
    BalanceSheetFigures,
    BalanceSheetPeriod,
    DeckElementFacts,
    DeckStructuralFacts,
    ModelLintFacts,
    NumericClaim,
    NumericClaimSet,
    SpecRoundTrip,
)

# A fixed, tz-aware instant a real ``datetime.now()`` could never return on this run,
# so a verdict carrying it PROVES the gate read the injected clock, not the wall clock.
_FIXED_TS = datetime(2017, 3, 4, 9, 30, tzinfo=UTC)

# The seven floor checks in the factory's registration (== run == checks_run) order.
_EXPECTED_ORDER = (
    ReviewCheckId.ACCOUNTING_IDENTITY,
    ReviewCheckId.SPEC_ROUND_TRIP,
    ReviewCheckId.NUMERIC_RECOMPUTE,
    ReviewCheckId.FILE_OPENS_CLEAN,
    ReviewCheckId.FAST_LINT,
    ReviewCheckId.IBCS_SUCCESS,
    ReviewCheckId.VISUAL_INTEGRITY,
)


def _fixed_clock() -> datetime:
    """A clock returning the constant ``_FIXED_TS`` so reviews are reproducible."""
    return _FIXED_TS


class _CountingClock:
    """A clock that returns a fixed instant and counts how often it was called."""

    def __init__(self, instant: datetime) -> None:
        self._instant = instant
        self.calls = 0

    def __call__(self) -> datetime:
        self.calls += 1
        return self._instant


class _CleanProbe:
    """A file-open probe that always reports a clean open (synthetic, no IO)."""

    def probe(self, path: Path, kind: ArtifactKind) -> tuple[bool, str]:
        return (True, "")


class _StubCheck:
    """A configurable check: returns canned findings, or raises a canned exception."""

    def __init__(
        self,
        check_id: ReviewCheckId,
        findings: tuple[ReviewFinding, ...] = (),
        exc: Exception | None = None,
    ) -> None:
        self._id = check_id
        self._findings = findings
        self._exc = exc

    @property
    def id(self) -> ReviewCheckId:
        return self._id

    def run(self, artifact: ReviewableArtifact) -> tuple[ReviewFinding, ...]:
        if self._exc is not None:
            raise self._exc
        return self._findings


def _existing_file(tmp_path: Path) -> Path:
    """Create and return a real on-disk file so FILE_OPENS_CLEAN sees it exists."""
    target = tmp_path / "artifact.bin"
    target.write_bytes(b"synthetic-bytes")
    return target


def _financial_model(
    path: Path,
    *,
    numeric_recomputed: str = "10",
    extracted_title: str = "Q4",
    orphan_cells: tuple[str, ...] = (),
    periods: tuple[tuple[str, str], ...] = (("FY24", "100"),),
) -> ReviewableArtifact:
    """Build a financial-model artifact; defaults are fully clean (every check silent).

    ``periods`` is ``(label, assets)`` pairs with fixed L=60/E=40, so an assets of
    ``"100"`` balances and any other value plants an ACCOUNTING_IDENTITY defect.
    """
    bs = BalanceSheetFigures(
        periods=tuple(
            BalanceSheetPeriod(
                period=label,
                assets=Decimal(amount),
                liabilities=Decimal("60"),
                equity=Decimal("40"),
            )
            for label, amount in periods
        )
    )
    return ReviewableArtifact(
        artifact_ref="model-001",
        kind=ArtifactKind.FINANCIAL_MODEL,
        path=path,
        balance_sheet=bs,
        numeric_claims=NumericClaimSet(
            claims=(
                NumericClaim(
                    label="rev",
                    declared_value=Decimal("10"),
                    recomputed_value=Decimal(numeric_recomputed),
                ),
            )
        ),
        spec_round_trip=SpecRoundTrip(
            declared_values={"title": "Q4"},
            extracted_values={"title": extracted_title},
        ),
        model_lint=ModelLintFacts(orphan_constant_cells=orphan_cells),
    )


# ---------------------------------------------------------------------------------
# Composition: a clean artifact passes; all seven checks ran in registration order.
# ---------------------------------------------------------------------------------
def test_clean_financial_model_passes_with_all_seven_checks_run(tmp_path: Path) -> None:
    gate = build_default_output_review_gate(_CleanProbe(), _fixed_clock)

    verdict = gate.review(_financial_model(_existing_file(tmp_path)))

    assert verdict.passed is True
    assert verdict.findings == ()
    assert verdict.checks_run == _EXPECTED_ORDER  # all seven, in registration order
    assert verdict.reviewed_at == _FIXED_TS


# ---------------------------------------------------------------------------------
# A planted blocking defect fails the verdict with the right check_id + locator.
# ---------------------------------------------------------------------------------
def test_planted_imbalance_blocks_with_accounting_finding(tmp_path: Path) -> None:
    gate = build_default_output_review_gate(_CleanProbe(), _fixed_clock)

    # Imbalanced FY24 (assets 99, L+E 100); every OTHER fact is clean, so the defect
    # is isolated to exactly one check — proving the gate surfaces THAT check's finding.
    artifact = _financial_model(_existing_file(tmp_path), periods=(("FY24", "99"),))
    verdict = gate.review(artifact)

    assert verdict.passed is False
    assert len(verdict.blocking_findings) == 1
    finding = verdict.blocking_findings[0]
    assert finding.check_id is ReviewCheckId.ACCOUNTING_IDENTITY
    assert finding.locator == "FY24"
    assert finding.severity is CheckSeverity.BLOCKING


# ---------------------------------------------------------------------------------
# Omission defence: an omitted mandatory check is absent from ``checks_run``.
# ---------------------------------------------------------------------------------
def test_omitted_check_is_detectable_from_checks_run(tmp_path: Path) -> None:
    from autofirm.output_review.accounting_identity_check import AccountingIdentityCheck
    from autofirm.output_review.fast_lint_check import FastLintCheck
    from autofirm.output_review.file_opens_clean_check import FileOpensCleanCheck
    from autofirm.output_review.ibcs_success_rubric_check import IbcsSuccessRubricCheck
    from autofirm.output_review.numeric_recomputation_check import (
        NumericRecomputationCheck,
    )
    from autofirm.output_review.spec_artifact_round_trip_check import SpecRoundTripCheck

    registry = CheckRegistry()
    # Register six of seven — deliberately OMIT VISUAL_INTEGRITY.
    registry.register(AccountingIdentityCheck())
    registry.register(SpecRoundTripCheck())
    registry.register(NumericRecomputationCheck())
    registry.register(FileOpensCleanCheck(_CleanProbe()))
    registry.register(FastLintCheck())
    registry.register(IbcsSuccessRubricCheck())
    gate = OutputReviewGate(registry, _fixed_clock)

    verdict = gate.review(_financial_model(_existing_file(tmp_path)))

    assert ReviewCheckId.VISUAL_INTEGRITY not in verdict.checks_run
    assert ReviewCheckId.ACCOUNTING_IDENTITY in verdict.checks_run
    assert len(verdict.checks_run) == 6


def test_empty_registry_review_raises_fail_closed(tmp_path: Path) -> None:
    gate = OutputReviewGate(CheckRegistry(), _fixed_clock)

    with pytest.raises(OutputReviewError):
        gate.review(_financial_model(_existing_file(tmp_path)))


# ---------------------------------------------------------------------------------
# Fail-closed on a raising check: it becomes a BLOCKING finding AND the next check
# still runs — no exception escapes ``review``.
# ---------------------------------------------------------------------------------
def test_raising_check_becomes_blocking_finding_and_others_still_run(
    tmp_path: Path,
) -> None:
    from autofirm.output_review.accounting_identity_check import AccountingIdentityCheck

    registry = CheckRegistry()
    # The raising stub is registered FIRST, the real check SECOND — so a passing run
    # proves execution CONTINUED past the crash (not merely that a crash was caught).
    registry.register(_StubCheck(ReviewCheckId.MODEL_ADVISORY, exc=RuntimeError("boom")))
    registry.register(AccountingIdentityCheck())
    gate = OutputReviewGate(registry, _fixed_clock)

    artifact = _financial_model(_existing_file(tmp_path), periods=(("FY24", "99"),))
    verdict = gate.review(artifact)

    assert verdict.passed is False
    assert len(verdict.findings) == 2  # crash finding + the real accounting finding
    crash, accounting = verdict.findings
    assert crash.check_id is ReviewCheckId.MODEL_ADVISORY
    assert crash.severity is CheckSeverity.BLOCKING
    assert crash.defect_class is DefectClass.EUREKA  # min of {EUREKA}
    assert "RuntimeError" in crash.message
    assert crash.locator == "model-001"  # the artifact ref
    # The check AFTER the crash still ran and produced its own real finding.
    assert accounting.check_id is ReviewCheckId.ACCOUNTING_IDENTITY
    assert accounting.locator == "FY24"


def test_crash_finding_defect_class_is_deterministic_min_for_multiclass(
    tmp_path: Path,
) -> None:
    registry = CheckRegistry()
    # FAST_LINT owns {MECHANICAL, OMISSION}; min-by-value must pick MECHANICAL every
    # run (M < O), so a crash finding is byte-identical regardless of set iteration.
    registry.register(_StubCheck(ReviewCheckId.FAST_LINT, exc=ValueError("x")))
    gate = OutputReviewGate(registry, _fixed_clock)

    verdict = gate.review(_financial_model(_existing_file(tmp_path)))

    assert len(verdict.findings) == 1
    expected = min(CHECK_DEFECT_CLASSES[ReviewCheckId.FAST_LINT], key=lambda d: d.value)
    assert verdict.findings[0].defect_class is expected is DefectClass.MECHANICAL
    assert "ValueError" in verdict.findings[0].message


# ---------------------------------------------------------------------------------
# Determinism: identical inputs + injected clock => byte-identical verdicts.
# ---------------------------------------------------------------------------------
def test_repeated_reviews_are_byte_identical(tmp_path: Path) -> None:
    gate = build_default_output_review_gate(_CleanProbe(), _fixed_clock)
    artifact = _financial_model(_existing_file(tmp_path), periods=(("FY24", "99"),))

    verdicts = [gate.review(artifact) for _ in range(5)]

    first = verdicts[0]
    for other in verdicts[1:]:
        assert other == first  # pydantic model equality => every field identical


def test_clock_is_injected_and_called_exactly_once_per_review(tmp_path: Path) -> None:
    clock = _CountingClock(_FIXED_TS)
    gate = build_default_output_review_gate(_CleanProbe(), clock)

    verdict = gate.review(_financial_model(_existing_file(tmp_path)))

    assert verdict.reviewed_at == _FIXED_TS  # came from the injected clock, not now()
    assert clock.calls == 1  # exactly one clock read per review (no hidden now() call)


# ---------------------------------------------------------------------------------
# Finding-order determinism: registry order outer, per-check order inner, stable.
# ---------------------------------------------------------------------------------
def test_multi_defect_findings_follow_registry_then_per_check_order(
    tmp_path: Path,
) -> None:
    gate = build_default_output_review_gate(_CleanProbe(), _fixed_clock)
    # Defects across FOUR checks at different registry positions, plus TWO imbalanced
    # periods to pin per-check (period) order within the first check.
    artifact = _financial_model(
        _existing_file(tmp_path),
        numeric_recomputed="11",  # NUMERIC_RECOMPUTE mismatch
        extracted_title="WRONG",  # SPEC_ROUND_TRIP mismatch
        orphan_cells=("Sheet1!B2",),  # FAST_LINT orphan
        periods=(("FY23", "1"), ("FY24", "2")),  # both imbalanced, in this order
    )

    runs = [gate.review(artifact) for _ in range(5)]
    sequences = [
        tuple((f.check_id, f.locator) for f in v.findings) for v in runs
    ]

    expected = (
        (ReviewCheckId.ACCOUNTING_IDENTITY, "FY23"),  # check 1, period order
        (ReviewCheckId.ACCOUNTING_IDENTITY, "FY24"),
        (ReviewCheckId.SPEC_ROUND_TRIP, "title"),  # check 2
        (ReviewCheckId.NUMERIC_RECOMPUTE, "rev"),  # check 3
        (ReviewCheckId.FAST_LINT, "Sheet1!B2"),  # check 5
    )
    assert sequences[0] == expected
    assert all(seq == expected for seq in sequences)  # stable across runs


# ---------------------------------------------------------------------------------
# Property A (stub checks, mixed severities): the gate NEVER manufactures a false
# pass — passed iff no BLOCKING finding — even when ADVISORY findings are present.
# ---------------------------------------------------------------------------------
@st.composite
def _stub_plan(
    draw: st.DrawFn,
) -> list[tuple[ReviewCheckId, tuple[ReviewFinding, ...]]]:
    ids = draw(
        st.lists(
            st.sampled_from(list(ReviewCheckId)),
            min_size=1,
            max_size=len(ReviewCheckId),
            unique=True,
        )
    )
    plan: list[tuple[ReviewCheckId, tuple[ReviewFinding, ...]]] = []
    for check_id in ids:
        count = draw(st.integers(min_value=0, max_value=3))
        findings = tuple(
            ReviewFinding(
                check_id=check_id,
                severity=draw(st.sampled_from(list(CheckSeverity))),
                defect_class=DefectClass.MECHANICAL,
                message="m",
                locator="l",
            )
            for _ in range(count)
        )
        plan.append((check_id, findings))
    return plan


@settings(max_examples=200)
@given(plan=_stub_plan())
def test_property_passed_iff_no_blocking_finding_over_stub_checks(
    plan: list[tuple[ReviewCheckId, tuple[ReviewFinding, ...]]],
) -> None:
    registry = CheckRegistry()
    for check_id, findings in plan:
        registry.register(_StubCheck(check_id, findings=findings))
    gate = OutputReviewGate(registry, _fixed_clock)
    artifact = ReviewableArtifact(
        artifact_ref="x", kind=ArtifactKind.FINANCIAL_MODEL, path=Path("unread")
    )

    verdict = gate.review(artifact)

    has_blocking = any(
        f.severity is CheckSeverity.BLOCKING
        for _, findings in plan
        for f in findings
    )
    assert verdict.passed is (not has_blocking)
    # The gate collected EVERY finding (none dropped) — count is conserved.
    assert len(verdict.findings) == sum(len(findings) for _, findings in plan)
    assert verdict.checks_run == tuple(cid for cid, _ in plan)


# ---------------------------------------------------------------------------------
# Property B (assorted real artifacts via the default gate): same invariant end-to-end.
# ---------------------------------------------------------------------------------
@st.composite
def _financial(draw: st.DrawFn, path: Path) -> ReviewableArtifact:
    balanced = "100" if draw(st.booleans()) else "101"
    return _financial_model(
        path,
        numeric_recomputed="10" if draw(st.booleans()) else "12",
        extracted_title="Q4" if draw(st.booleans()) else "BAD",
        orphan_cells=() if draw(st.booleans()) else ("A1",),
        periods=(("FY24", balanced),),
    )


@st.composite
def _deck(draw: st.DrawFn, path: Path) -> ReviewableArtifact:
    count = draw(st.integers(min_value=1, max_value=4))
    elements = tuple(
        DeckElementFacts(
            element_id=f"slide#{i}",
            element_kind="BAR_CHART",
            has_notation=draw(st.booleans()),
            has_units=draw(st.booleans()),
            has_overlap=draw(st.booleans()),
            has_clipping=draw(st.booleans()),
            axis_truncated=draw(st.booleans()),
        )
        for i in range(count)
    )
    return ReviewableArtifact(
        artifact_ref="deck-001",
        kind=ArtifactKind.SLIDE_DECK,
        path=path,
        spec_round_trip=SpecRoundTrip(
            declared_values={"t": "x"}, extracted_values={"t": "x"}
        ),
        deck_facts=DeckStructuralFacts(elements=elements),
    )


def test_property_passed_iff_no_blocking_finding_over_assorted_artifacts(
    tmp_path: Path,
) -> None:
    path = _existing_file(tmp_path)
    gate = build_default_output_review_gate(_CleanProbe(), _fixed_clock)
    artifacts = st.one_of(_financial(path), _deck(path))

    @settings(max_examples=200)
    @given(artifact=artifacts)
    def _check(artifact: ReviewableArtifact) -> None:
        verdict = gate.review(artifact)
        has_blocking = any(
            f.severity is CheckSeverity.BLOCKING for f in verdict.findings
        )
        assert verdict.passed is (not has_blocking)
        assert verdict.blocking_findings == tuple(
            f for f in verdict.findings if f.severity is CheckSeverity.BLOCKING
        )

    _check()
