"""The labelled synthetic golden corpus: one planted defect per relevant check.

What this does
--------------
Builds a *labelled* corpus of :class:`ReviewableArtifact` cases the efficacy
harness runs the deterministic gate over. Each case carries a ground-truth label —
whether it is a known-good control or which Panko-Halverson defect class was
planted, and which check should catch it — so the harness can measure a real
defect-detection rate, escape rate, and false-positive rate (CLAUDE.md §3.10).

Planted defects (one per relevant check / defect class)
-------------------------------------------------------
* ACCOUNTING_IDENTITY  — off-by-0.01 balance (A != L + E)            [PURE_LOGIC]
* NUMERIC_RECOMPUTE     — declared figure != independent recompute   [MECHANICAL]
* SPEC_ROUND_TRIP       — a spec value altered / missing / extra      [MECHANICAL]
* FAST_LINT             — orphan constant / inconsistent row /
                          missing line-item                          [MECHANICAL/OMISSION]
* IBCS_SUCCESS          — missing IBCS notation / missing units       [PURE_LOGIC]
* VISUAL_INTEGRITY      — truncated axis / overlap / clipping          [PURE_LOGIC]
* FILE_OPENS_CLEAN      — corrupt OOXML (file will not open clean)     [MECHANICAL]

EUREKA (wrong domain model) is deliberately NOT planted as must-block: the research
floor provably cannot reach it deterministically (it is the sole residue routed to
the advisory model layer), so planting it as must-block would misrepresent the
gate. Controls span all three artifact kinds so a false positive on any kind shows.

No real data (CLAUDE.md §3.12)
------------------------------
Every figure, label, and file is synthetic. Files are minimal OOXML containers the
probe opens structurally; no real client artifact is ever read.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from autofirm.output_review import (
    ArtifactKind,
    BalanceSheetFigures,
    BalanceSheetPeriod,
    DeckElementFacts,
    DeckStructuralFacts,
    DefectClass,
    ModelLintFacts,
    ModelRowFormulaFacts,
    NumericClaim,
    NumericClaimSet,
    ReviewableArtifact,
    ReviewCheckId,
    SpecRoundTrip,
)

from ooxml_file_open_probe import (  # flat sibling import (script dir on sys.path)
    write_corrupt_ooxml,
    write_valid_ooxml,
)

__all__ = ["GoldenCase", "build_corpus"]


@dataclass(frozen=True)
class GoldenCase:
    """One labelled corpus entry: the artifact plus its ground-truth verdict.

    Attributes:
        case_id: Stable, human-readable id (used in the per-case CSV and graphs).
        description: One line on what the case is / what was planted.
        artifact: The :class:`ReviewableArtifact` the gate reviews.
        is_control: ``True`` for a known-good control (must PASS); ``False`` for a
            planted-defect case (must BLOCK).
        planted_class: The Panko-Halverson :class:`DefectClass` planted (``None`` for
            controls). Used to bucket the per-class detection rate.
        planted_check: The :class:`ReviewCheckId` that should catch it (``None`` for
            controls), so the harness can confirm the RIGHT check fired.
    """

    case_id: str
    description: str
    artifact: ReviewableArtifact
    is_control: bool
    planted_class: DefectClass | None
    planted_check: ReviewCheckId | None


# --- clean, balanced fact bundles every model case starts from (then one is broken) ---
def _clean_balance() -> BalanceSheetFigures:
    """A balanced two-period balance sheet (A == L + E exact)."""
    return BalanceSheetFigures(
        periods=(
            BalanceSheetPeriod(
                period="FY24",
                assets=Decimal("1000.00"),
                liabilities=Decimal("600.00"),
                equity=Decimal("400.00"),
            ),
            BalanceSheetPeriod(
                period="FY25",
                assets=Decimal("1250.00"),
                liabilities=Decimal("700.00"),
                equity=Decimal("550.00"),
            ),
        )
    )


def _clean_numeric() -> NumericClaimSet:
    """Numeric claims whose declared values match their independent recompute."""
    return NumericClaimSet(
        claims=(
            NumericClaim(
                label="gross_margin_fy24",
                declared_value=Decimal("0.42"),
                recomputed_value=Decimal("0.42"),
            ),
            NumericClaim(
                label="total_assets_fy25",
                declared_value=Decimal("1250.00"),
                recomputed_value=Decimal("1250.00"),
            ),
        )
    )


def _clean_round_trip() -> SpecRoundTrip:
    """A spec round-trip where every declared value survived into the artifact."""
    declared = {"company": "ACME-SYNTH", "currency": "USD", "fy": "2025"}
    return SpecRoundTrip(declared_values=dict(declared), extracted_values=dict(declared))


def _clean_model_lint() -> ModelLintFacts:
    """Lint facts with no orphan constants, consistent rows, no omissions."""
    return ModelLintFacts(
        orphan_constant_cells=(),
        rows=(
            ModelRowFormulaFacts(row_label="Revenue", formula_consistent=True),
            ModelRowFormulaFacts(row_label="COGS", formula_consistent=True),
        ),
        present_line_items=frozenset({"Revenue", "COGS", "GrossProfit"}),
        expected_line_items=frozenset({"Revenue", "COGS", "GrossProfit"}),
    )


def _clean_deck() -> DeckStructuralFacts:
    """A deck whose elements satisfy IBCS notation/units and have no layout defects."""
    return DeckStructuralFacts(
        elements=(
            DeckElementFacts(
                element_id="slide#1/chart#1",
                element_kind="BAR_CHART",
                has_notation=True,
                has_units=True,
            ),
            DeckElementFacts(
                element_id="slide#2/chart#1",
                element_kind="LINE_CHART",
                has_notation=True,
                has_units=True,
            ),
        )
    )


def _model(ref: str, path: Path, **overrides: object) -> ReviewableArtifact:
    """Build a FINANCIAL_MODEL artifact from clean bundles, overriding one to plant."""
    bundles: dict[str, object] = {
        "balance_sheet": _clean_balance(),
        "numeric_claims": _clean_numeric(),
        "spec_round_trip": _clean_round_trip(),
        "model_lint": _clean_model_lint(),
    }
    bundles.update(overrides)
    return ReviewableArtifact(
        artifact_ref=ref, kind=ArtifactKind.FINANCIAL_MODEL, path=path, **bundles
    )


def _deck(ref: str, path: Path, deck: DeckStructuralFacts) -> ReviewableArtifact:
    """Build a SLIDE_DECK artifact (round-trip clean) with the given deck facts."""
    return ReviewableArtifact(
        artifact_ref=ref,
        kind=ArtifactKind.SLIDE_DECK,
        path=path,
        spec_round_trip=_clean_round_trip(),
        deck_facts=deck,
    )


def _deck_with(ref: str, path: Path, **flag: object) -> ReviewableArtifact:
    """A deck whose first element has one flag flipped to plant a single defect."""
    element_flags: dict[str, object] = {"has_notation": True, "has_units": True}
    element_flags.update(flag)  # the planted flag overrides exactly one default
    first = DeckElementFacts(
        element_id="slide#1/chart#1",
        element_kind="BAR_CHART",
        **element_flags,
    )
    rest = _clean_deck().elements[1:]
    return _deck(ref, path, DeckStructuralFacts(elements=(first, *rest)))


def build_corpus(workdir: Path) -> list[GoldenCase]:  # noqa: PLR0915 (flat case list)
    """Materialise the synthetic files under ``workdir`` and return labelled cases.

    Writes a valid OOXML container per case (and one corrupt file for the
    FILE_OPENS_CLEAN plant), then builds the labelled :class:`GoldenCase` list. The
    files are synthetic and live only under ``workdir`` (CLAUDE.md §3.12).
    """
    ok = workdir / "valid.xlsx"
    write_valid_ooxml(ok)
    deck_ok = workdir / "valid.pptx"
    write_valid_ooxml(deck_ok)
    doc_ok = workdir / "valid.docx"
    write_valid_ooxml(doc_ok)
    corrupt = workdir / "corrupt.xlsx"
    write_corrupt_ooxml(corrupt)

    cases: list[GoldenCase] = []

    def control(cid: str, desc: str, art: ReviewableArtifact) -> None:
        cases.append(GoldenCase(cid, desc, art, True, None, None))

    def plant(
        cid: str,
        desc: str,
        art: ReviewableArtifact,
        cls: DefectClass,
        check: ReviewCheckId,
    ) -> None:
        cases.append(GoldenCase(cid, desc, art, False, cls, check))

    # --- known-good controls across all three artifact kinds (must PASS) ---
    control("control_model_clean_a", "clean financial model", _model("ref-cm-a", ok))
    control(
        "control_model_clean_b",
        "clean financial model (different figures)",
        _model(
            "ref-cm-b",
            ok,
            numeric_claims=NumericClaimSet(
                claims=(
                    NumericClaim(
                        label="ebitda_fy25",
                        declared_value=Decimal("310.50"),
                        recomputed_value=Decimal("310.50"),
                    ),
                )
            ),
        ),
    )
    control("control_deck_clean", "clean slide deck", _deck("ref-cd", deck_ok, _clean_deck()))
    control(
        "control_document_clean",
        "clean business document",
        ReviewableArtifact(
            artifact_ref="ref-doc",
            kind=ArtifactKind.BUSINESS_DOCUMENT,
            path=doc_ok,
            spec_round_trip=_clean_round_trip(),
        ),
    )

    # --- planted defects: one per relevant check / defect class (must BLOCK) ---
    imbalanced = BalanceSheetFigures(
        periods=(
            BalanceSheetPeriod(
                period="FY24",
                assets=Decimal("1000.01"),  # off by 0.01: A != L + E
                liabilities=Decimal("600.00"),
                equity=Decimal("400.00"),
            ),
        )
    )
    plant(
        "plant_balance_off_by_0_01",
        "balance sheet off by 0.01 (A != L + E)",
        _model("ref-bal", ok, balance_sheet=imbalanced),
        DefectClass.PURE_LOGIC,
        ReviewCheckId.ACCOUNTING_IDENTITY,
    )
    plant(
        "plant_numeric_recompute_mismatch",
        "declared figure != independent recomputation",
        _model(
            "ref-num",
            ok,
            numeric_claims=NumericClaimSet(
                claims=(
                    NumericClaim(
                        label="gross_margin_fy24",
                        declared_value=Decimal("0.42"),
                        recomputed_value=Decimal("0.39"),  # mismatch
                    ),
                )
            ),
        ),
        DefectClass.MECHANICAL,
        ReviewCheckId.NUMERIC_RECOMPUTE,
    )
    plant(
        "plant_spec_value_altered",
        "spec value altered in the rendered artifact",
        _model(
            "ref-rt-alt",
            ok,
            spec_round_trip=SpecRoundTrip(
                declared_values={"company": "ACME-SYNTH", "currency": "USD"},
                extracted_values={"company": "ACME-SYNTH", "currency": "EUR"},  # altered
            ),
        ),
        DefectClass.MECHANICAL,
        ReviewCheckId.SPEC_ROUND_TRIP,
    )
    plant(
        "plant_spec_value_missing",
        "declared spec value dropped from the artifact",
        _model(
            "ref-rt-miss",
            ok,
            spec_round_trip=SpecRoundTrip(
                declared_values={"company": "ACME-SYNTH", "currency": "USD"},
                extracted_values={"company": "ACME-SYNTH"},  # currency dropped
            ),
        ),
        DefectClass.MECHANICAL,
        ReviewCheckId.SPEC_ROUND_TRIP,
    )
    plant(
        "plant_spec_value_extra",
        "artifact carries a value the spec never declared",
        _model(
            "ref-rt-extra",
            ok,
            spec_round_trip=SpecRoundTrip(
                declared_values={"company": "ACME-SYNTH"},
                extracted_values={"company": "ACME-SYNTH", "watermark": "DRAFT"},  # extra
            ),
        ),
        DefectClass.MECHANICAL,
        ReviewCheckId.SPEC_ROUND_TRIP,
    )
    plant(
        "plant_orphan_constant_cell",
        "hard-coded constant where a formula belongs",
        _model(
            "ref-orphan",
            ok,
            model_lint=ModelLintFacts(
                orphan_constant_cells=("Model!C7",),
                rows=_clean_model_lint().rows,
                present_line_items=_clean_model_lint().present_line_items,
                expected_line_items=_clean_model_lint().expected_line_items,
            ),
        ),
        DefectClass.MECHANICAL,
        ReviewCheckId.FAST_LINT,
    )
    plant(
        "plant_inconsistent_row",
        "a row whose cells do not share the row formula",
        _model(
            "ref-row",
            ok,
            model_lint=ModelLintFacts(
                rows=(
                    ModelRowFormulaFacts(row_label="Revenue", formula_consistent=True),
                    ModelRowFormulaFacts(row_label="COGS", formula_consistent=False),
                ),
                present_line_items=_clean_model_lint().present_line_items,
                expected_line_items=_clean_model_lint().expected_line_items,
            ),
        ),
        DefectClass.MECHANICAL,
        ReviewCheckId.FAST_LINT,
    )
    plant(
        "plant_missing_line_item",
        "a required line-item omitted from the model",
        _model(
            "ref-omit",
            ok,
            model_lint=ModelLintFacts(
                rows=_clean_model_lint().rows,
                present_line_items=frozenset({"Revenue", "COGS"}),  # GrossProfit omitted
                expected_line_items=frozenset({"Revenue", "COGS", "GrossProfit"}),
            ),
        ),
        DefectClass.OMISSION,
        ReviewCheckId.FAST_LINT,
    )
    plant(
        "plant_missing_ibcs_notation",
        "IBCS notation absent where required",
        _deck_with("ref-ibcs-n", deck_ok, has_notation=False),
        DefectClass.PURE_LOGIC,
        ReviewCheckId.IBCS_SUCCESS,
    )
    plant(
        "plant_missing_units",
        "axis/value units unlabelled",
        _deck_with("ref-ibcs-u", deck_ok, has_units=False),
        DefectClass.PURE_LOGIC,
        ReviewCheckId.IBCS_SUCCESS,
    )
    plant(
        "plant_truncated_axis",
        "value axis truncated / not zero-based (misleading)",
        _deck_with("ref-vis-axis", deck_ok, axis_truncated=True),
        DefectClass.PURE_LOGIC,
        ReviewCheckId.VISUAL_INTEGRITY,
    )
    plant(
        "plant_overlapping_elements",
        "overlapping slide elements (layout defect)",
        _deck_with("ref-vis-ovl", deck_ok, has_overlap=True),
        DefectClass.PURE_LOGIC,
        ReviewCheckId.VISUAL_INTEGRITY,
    )
    plant(
        "plant_clipped_content",
        "clipped / truncated content (layout defect)",
        _deck_with("ref-vis-clip", deck_ok, has_clipping=True),
        DefectClass.PURE_LOGIC,
        ReviewCheckId.VISUAL_INTEGRITY,
    )
    plant(
        "plant_corrupt_ooxml",
        "corrupt OOXML file that will not open clean",
        _model("ref-corrupt", corrupt),  # bundles clean; only the FILE bytes are bad
        DefectClass.MECHANICAL,
        ReviewCheckId.FILE_OPENS_CLEAN,
    )

    return cases
