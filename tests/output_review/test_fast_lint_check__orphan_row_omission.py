"""Teeth-tests for the FAST_LINT deterministic floor check (orphan / row / omission).

Prove (CLAUDE.md §3.6, §5.6, §3.11): each of the three defect families is detected
*independently* at the exact locator with the exact defect class, a clean model
yields ``()`` (no false defect), an absent fact bundle fails CLOSED with a single
BLOCKING OMISSION finding, a non-applicable artifact kind yields ``()``, findings
are emitted in a fixed, reproducible order (orphans -> rows -> sorted missing), and
``FastLintCheck`` satisfies the runtime-checkable ``ReviewCheck`` Protocol.

Property tests (hypothesis) assert the general invariants over random inputs: any
clean model is always ``()``, and injecting exactly one defect always yields exactly
one finding of the matching class and locator. No assertion here is tautological —
each would FAIL if the check mis-classified, mis-located, mis-ordered, or waved a
defect through.
"""

from __future__ import annotations

from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from autofirm.output_review.fast_lint_check import FastLintCheck
from autofirm.output_review.review_check_protocol import ReviewCheck
from autofirm.output_review.review_finding_and_severity_contracts import (
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
)
from autofirm.output_review.reviewable_artifact_contract import (
    ArtifactKind,
    ReviewableArtifact,
)
from autofirm.output_review.reviewable_artifact_facts import (
    ModelLintFacts,
    ModelRowFormulaFacts,
)

# Synthetic only; no filesystem I/O happens (the check never reads ``path``).
_SYNTH_PATH = Path("synthetic") / "model.xlsx"
# Non-blank token alphabet so generated cell/row/item names always survive the
# contract's non-blank validators (whitespace excluded -> never blank after strip).
_TOKENS = st.text(alphabet="abcdefgABCDEFG0123456789", min_size=1, max_size=6)


def _artifact(
    *,
    kind: ArtifactKind = ArtifactKind.FINANCIAL_MODEL,
    model_lint: ModelLintFacts | None = None,
    ref: str = "artifact#ref",
) -> ReviewableArtifact:
    """Build a synthetic reviewable artifact wrapping the given lint facts."""
    return ReviewableArtifact(
        artifact_ref=ref, kind=kind, path=_SYNTH_PATH, model_lint=model_lint
    )


def _consistent_rows(*labels: str) -> tuple[ModelRowFormulaFacts, ...]:
    return tuple(ModelRowFormulaFacts(row_label=lbl, formula_consistent=True) for lbl in labels)


# ---- Protocol conformance ------------------------------------------------------


def test_fast_lint_check_satisfies_review_check_protocol() -> None:
    # The gate composes checks via the runtime-checkable Protocol; a check that does
    # not conform would be silently unusable, so prove conformance explicitly.
    assert isinstance(FastLintCheck(), ReviewCheck)


def test_id_is_fast_lint() -> None:
    assert FastLintCheck().id is ReviewCheckId.FAST_LINT


# ---- applicability gates -------------------------------------------------------


def test_non_financial_kind_returns_empty_even_with_lint_facts() -> None:
    # A deck/document is out of scope for FAST_LINT; even if lint facts are present
    # (caller error), the check must not invent a defect on the wrong kind.
    facts = ModelLintFacts(orphan_constant_cells=("Sheet1!B2",))
    out = FastLintCheck().run(_artifact(kind=ArtifactKind.SLIDE_DECK, model_lint=facts))
    assert out == ()


def test_absent_facts_fail_closed_single_blocking_omission() -> None:
    # fail-closed: a financial model with NO lint facts cannot be verified and must
    # NOT read as clean — exactly one BLOCKING OMISSION finding at the artifact ref.
    out = FastLintCheck().run(_artifact(model_lint=None, ref="absent#42"))
    assert len(out) == 1
    finding = out[0]
    assert finding.check_id is ReviewCheckId.FAST_LINT
    assert finding.severity is CheckSeverity.BLOCKING
    assert finding.defect_class is DefectClass.OMISSION
    assert finding.locator == "absent#42"
    assert finding.message == "FAST lint facts absent — cannot verify"


# ---- clean model ---------------------------------------------------------------


def test_clean_model_returns_empty() -> None:
    # No orphans, all rows consistent, present is a SUPERSET of expected -> no defect.
    facts = ModelLintFacts(
        orphan_constant_cells=(),
        rows=_consistent_rows("Revenue", "COGS"),
        present_line_items=frozenset({"Revenue", "COGS", "EBITDA"}),
        expected_line_items=frozenset({"Revenue", "COGS"}),
    )
    assert FastLintCheck().run(_artifact(model_lint=facts)) == ()


# ---- single-defect detection, each class independently -------------------------


def test_single_orphan_constant_one_mechanical_at_cell() -> None:
    facts = ModelLintFacts(orphan_constant_cells=("Sheet1!C9",))
    out = FastLintCheck().run(_artifact(model_lint=facts))
    assert len(out) == 1
    assert out[0].defect_class is DefectClass.MECHANICAL
    assert out[0].severity is CheckSeverity.BLOCKING
    assert out[0].locator == "Sheet1!C9"
    assert out[0].message == "hard-coded constant where a formula belongs"


def test_single_inconsistent_row_one_mechanical_at_row_label() -> None:
    facts = ModelLintFacts(
        rows=(
            ModelRowFormulaFacts(row_label="GrossProfit", formula_consistent=True),
            ModelRowFormulaFacts(row_label="Opex", formula_consistent=False),
        )
    )
    out = FastLintCheck().run(_artifact(model_lint=facts))
    assert len(out) == 1
    assert out[0].defect_class is DefectClass.MECHANICAL
    assert out[0].locator == "Opex"
    assert out[0].message == "row formula inconsistent"


def test_single_missing_line_item_one_omission_at_item() -> None:
    facts = ModelLintFacts(
        present_line_items=frozenset({"Revenue"}),
        expected_line_items=frozenset({"Revenue", "CashFlowStatement"}),
    )
    out = FastLintCheck().run(_artifact(model_lint=facts))
    assert len(out) == 1
    assert out[0].defect_class is DefectClass.OMISSION
    assert out[0].locator == "CashFlowStatement"
    assert out[0].message == "required line-item/statement missing"


def test_consistent_row_does_not_fire() -> None:
    # Boundary: a row that IS consistent must produce no finding (no over-reporting).
    facts = ModelLintFacts(rows=_consistent_rows("Revenue"))
    assert FastLintCheck().run(_artifact(model_lint=facts)) == ()


def test_present_superset_of_expected_no_omission() -> None:
    # Extra present line-items beyond expected are fine; only MISSING expected fire.
    facts = ModelLintFacts(
        present_line_items=frozenset({"A", "B", "C"}),
        expected_line_items=frozenset({"A", "B"}),
    )
    assert FastLintCheck().run(_artifact(model_lint=facts)) == ()


# ---- combined defects: count, classes, and deterministic order -----------------


def test_combined_defects_grouped_and_ordered() -> None:
    # orphans (given order) -> inconsistent rows (given order) -> missing (sorted).
    facts = ModelLintFacts(
        orphan_constant_cells=("Z9", "A1"),  # NOT sorted: prove given order kept
        rows=(
            ModelRowFormulaFacts(row_label="r2", formula_consistent=False),
            ModelRowFormulaFacts(row_label="r1", formula_consistent=True),
            ModelRowFormulaFacts(row_label="r0", formula_consistent=False),
        ),
        present_line_items=frozenset({"keep"}),
        expected_line_items=frozenset({"keep", "Zeta", "Alpha"}),  # missing: Alpha,Zeta
    )
    out = FastLintCheck().run(_artifact(model_lint=facts))
    classes = [(f.defect_class, f.locator) for f in out]
    assert classes == [
        (DefectClass.MECHANICAL, "Z9"),  # orphan, given order
        (DefectClass.MECHANICAL, "A1"),
        (DefectClass.MECHANICAL, "r2"),  # inconsistent rows, given order (r0 after r2)
        (DefectClass.MECHANICAL, "r0"),
        (DefectClass.OMISSION, "Alpha"),  # missing, sorted (Alpha before Zeta)
        (DefectClass.OMISSION, "Zeta"),
    ]
    assert all(f.severity is CheckSeverity.BLOCKING for f in out)
    assert all(f.check_id is ReviewCheckId.FAST_LINT for f in out)


def test_determinism_repeated_runs_identical() -> None:
    facts = ModelLintFacts(
        orphan_constant_cells=("c1", "c2"),
        rows=(ModelRowFormulaFacts(row_label="r", formula_consistent=False),),
        present_line_items=frozenset({"p"}),
        expected_line_items=frozenset({"p", "y", "x", "z"}),
    )
    art = _artifact(model_lint=facts)
    first = FastLintCheck().run(art)
    second = FastLintCheck().run(art)
    assert first == second  # frozen pydantic models compare by value
    # missing items sorted stably regardless of frozenset iteration order:
    missing_locators = [f.locator for f in first if f.defect_class is DefectClass.OMISSION]
    assert missing_locators == ["x", "y", "z"]


# ---- property-based invariants -------------------------------------------------


@st.composite
def _clean_facts(draw: st.DrawFn) -> ModelLintFacts:
    """Random CLEAN facts: no orphans, all rows consistent, present superset expected."""
    present = draw(st.lists(_TOKENS, unique=True, max_size=6))
    expected_src = draw(st.lists(st.sampled_from(present), unique=True)) if present else []
    rows = _consistent_rows(*draw(st.lists(_TOKENS, unique=True, max_size=5)))
    return ModelLintFacts(
        orphan_constant_cells=(),
        rows=rows,
        present_line_items=frozenset(present),
        expected_line_items=frozenset(expected_src),
    )


@settings(max_examples=200, deadline=None)
@given(facts=_clean_facts())
def test_property_clean_facts_always_empty(facts: ModelLintFacts) -> None:
    assert FastLintCheck().run(_artifact(model_lint=facts)) == ()


@settings(max_examples=200, deadline=None)
@given(facts=_clean_facts(), cell=_TOKENS)
def test_property_injected_orphan_yields_one_mechanical(
    facts: ModelLintFacts, cell: str
) -> None:
    injected = facts.model_copy(update={"orphan_constant_cells": (cell,)})
    out = FastLintCheck().run(_artifact(model_lint=injected))
    assert len(out) == 1
    assert out[0].defect_class is DefectClass.MECHANICAL
    assert out[0].locator == cell
    assert out[0].severity is CheckSeverity.BLOCKING


@settings(max_examples=200, deadline=None)
@given(facts=_clean_facts(), label=_TOKENS)
def test_property_injected_inconsistent_row_yields_one_mechanical(
    facts: ModelLintFacts, label: str
) -> None:
    bad = ModelRowFormulaFacts(row_label=label, formula_consistent=False)
    injected = facts.model_copy(update={"rows": (*facts.rows, bad)})
    out = FastLintCheck().run(_artifact(model_lint=injected))
    assert len(out) == 1
    assert out[0].defect_class is DefectClass.MECHANICAL
    assert out[0].locator == label


@settings(max_examples=200, deadline=None)
@given(facts=_clean_facts(), name=_TOKENS)
def test_property_injected_missing_item_yields_one_omission(
    facts: ModelLintFacts, name: str
) -> None:
    assume(name not in facts.present_line_items)  # ensure it is genuinely missing
    injected = facts.model_copy(
        update={"expected_line_items": facts.expected_line_items | {name}}
    )
    out = FastLintCheck().run(_artifact(model_lint=injected))
    assert len(out) == 1
    assert out[0].defect_class is DefectClass.OMISSION
    assert out[0].locator == name
