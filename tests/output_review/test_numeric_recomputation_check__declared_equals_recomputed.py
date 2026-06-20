"""Teeth-tests for :class:`NumericRecomputationCheck` (NUMERIC_RECOMPUTE).

Prove (CLAUDE.md §3.6, §3.11, §5.6) that the check actually has teeth — every test
asserts a failure the check MUST catch or a pass it MUST grant, none tautological:

* **boundary-exact:** a declared figure off by ``Decimal("0.01")`` (either side) is a
  BLOCKING defect; exact numeric equality (incl. trailing-zero representations) passes.
* **property-based (hypothesis):** for random bounded ``Decimal`` figures, declared==
  recomputed always yields no findings; a non-zero injected delta always yields exactly
  one BLOCKING finding whose locator is that claim's label and whose expected/actual
  carry the exact recomputed/declared pair.
* **stale-constant scenario:** a builder that wrote a hard-coded constant where the
  recomputation differs is flagged (the MECHANICAL defect this check exists to kill).
* **selectivity:** a multi-claim model with exactly one wrong figure yields exactly one
  finding at the correct locator, in claim order; all-equal yields ().
* **fail-closed:** a financial model with no numeric-claim facts yields one BLOCKING
  finding (cannot verify); a non-financial kind declines with () even if claims are set.
* **determinism + protocol:** N repeats are identical; the check satisfies the
  runtime-checkable :class:`ReviewCheck` Protocol.

Synthetic data only; no network, no file I/O (the ``path`` is never opened here).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from autofirm.output_review.numeric_recomputation_check import (
    NumericRecomputationCheck,
)
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
    NumericClaim,
    NumericClaimSet,
)

# A synthetic on-disk reference; this check never opens the file, so it is never read.
_SYNTHETIC_PATH = Path("synthetic") / "model.xlsx"


def _claim(label: str, declared: Decimal, recomputed: Decimal) -> NumericClaim:
    """Build one synthetic declared-vs-recomputed numeric claim."""
    return NumericClaim(
        label=label, declared_value=declared, recomputed_value=recomputed
    )


def _model(
    claims: tuple[NumericClaim, ...] | None,
    *,
    ref: str = "artifact#hash-abc",
    kind: ArtifactKind = ArtifactKind.FINANCIAL_MODEL,
) -> ReviewableArtifact:
    """Build a synthetic reviewable artifact (financial model by default)."""
    claim_set = NumericClaimSet(claims=claims) if claims is not None else None
    return ReviewableArtifact(
        artifact_ref=ref,
        kind=kind,
        path=_SYNTHETIC_PATH,
        numeric_claims=claim_set,
    )


# ---- protocol conformance ------------------------------------------------------


def test_check_satisfies_review_check_protocol() -> None:
    # runtime_checkable: proves `id` + `run` are present with the right shape.
    assert isinstance(NumericRecomputationCheck(), ReviewCheck)


def test_id_is_numeric_recompute() -> None:
    assert NumericRecomputationCheck().id is ReviewCheckId.NUMERIC_RECOMPUTE


def test_declared_defect_class_is_within_canonical_map() -> None:
    # The finding's defect_class must be a member of the canonical check->class map,
    # so the evidence showcase reports it against the same source of truth (§3.10).
    finding = NumericRecomputationCheck().run(
        _model((_claim("gm", Decimal("100"), Decimal("99")),))
    )[0]
    assert finding.defect_class in CHECK_DEFECT_CLASSES[ReviewCheckId.NUMERIC_RECOMPUTE]
    assert finding.defect_class is DefectClass.MECHANICAL


# ---- boundary: exact equality passes, off-by-0.01 fails ------------------------


def test_exact_equality_passes() -> None:
    out = NumericRecomputationCheck().run(
        _model((_claim("gm", Decimal("100.00"), Decimal("100.00")),))
    )
    assert out == ()


def test_trailing_zero_representation_is_numeric_equality_not_string() -> None:
    # 100.0 and 100.00 are the same VALUE — a stale-string false positive would be a bug.
    out = NumericRecomputationCheck().run(
        _model((_claim("gm", Decimal("100.0"), Decimal("100.00")),))
    )
    assert out == ()


@pytest.mark.parametrize(
    ("declared", "recomputed"),
    [
        (Decimal("100.01"), Decimal("100.00")),  # just over
        (Decimal("99.99"), Decimal("100.00")),  # just under
        (Decimal("100.00"), Decimal("100.01")),  # recomputed just over
    ],
)
def test_off_by_one_cent_is_blocking(declared: Decimal, recomputed: Decimal) -> None:
    out = NumericRecomputationCheck().run(
        _model((_claim("gm", declared, recomputed),))
    )
    assert len(out) == 1
    f = out[0]
    assert f.severity is CheckSeverity.BLOCKING
    assert f.check_id is ReviewCheckId.NUMERIC_RECOMPUTE
    assert f.locator == "gm"
    assert f.expected == f"recomputed={recomputed}"
    assert f.actual == f"declared={declared}"


# ---- stale-constant scenario (the MECHANICAL defect this check kills) ----------


def test_hard_coded_stale_constant_is_flagged() -> None:
    # A builder froze last year's figure (1_000_000) where this year recomputes to
    # 1_250_000 — exactly the hard-coded-where-formula-belongs defect (Panko-Halverson).
    out = NumericRecomputationCheck().run(
        _model((_claim("revenue_fy25", Decimal("1000000"), Decimal("1250000")),))
    )
    assert len(out) == 1
    assert out[0].defect_class is DefectClass.MECHANICAL
    assert out[0].locator == "revenue_fy25"
    assert out[0].expected == "recomputed=1250000"
    assert out[0].actual == "declared=1000000"


# ---- selectivity: exactly one wrong among many ---------------------------------


def test_multi_claim_exactly_one_wrong_yields_one_finding() -> None:
    claims = (
        _claim("a", Decimal("10"), Decimal("10")),
        _claim("b", Decimal("21"), Decimal("20")),  # the one wrong claim
        _claim("c", Decimal("30"), Decimal("30")),
    )
    out = NumericRecomputationCheck().run(_model(claims))
    assert len(out) == 1
    assert out[0].locator == "b"


def test_all_equal_yields_no_findings() -> None:
    claims = tuple(
        _claim(label, Decimal(v), Decimal(v))
        for label, v in (("a", "10"), ("b", "20"), ("c", "30"))
    )
    assert NumericRecomputationCheck().run(_model(claims)) == ()


def test_findings_follow_claim_order() -> None:
    # Two wrong claims must surface in the order the artifact presents them.
    claims = (
        _claim("first", Decimal("1"), Decimal("2")),
        _claim("ok", Decimal("5"), Decimal("5")),
        _claim("second", Decimal("9"), Decimal("8")),
    )
    out = NumericRecomputationCheck().run(_model(claims))
    assert [f.locator for f in out] == ["first", "second"]


# ---- fail-closed: absent facts and out-of-scope kinds --------------------------


def test_absent_numeric_claims_on_financial_model_is_blocking() -> None:
    out = NumericRecomputationCheck().run(_model(None, ref="artifact#missing-facts"))
    assert len(out) == 1
    f = out[0]
    assert f.severity is CheckSeverity.BLOCKING
    assert f.defect_class is DefectClass.MECHANICAL
    assert f.check_id is ReviewCheckId.NUMERIC_RECOMPUTE
    assert f.locator == "artifact#missing-facts"  # locator is the artifact ref
    assert "absent" in f.message
    assert f.expected is None and f.actual is None


@pytest.mark.parametrize(
    "kind", [ArtifactKind.SLIDE_DECK, ArtifactKind.BUSINESS_DOCUMENT]
)
def test_non_financial_kind_declines_even_with_wrong_claims(
    kind: ArtifactKind,
) -> None:
    # The kind gate must precede the claim check: a deck/document with a wrong claim
    # is still out of scope and must return () (no NUMERIC_RECOMPUTE finding leaks).
    out = NumericRecomputationCheck().run(
        _model((_claim("x", Decimal("1"), Decimal("2")),), kind=kind)
    )
    assert out == ()


def test_non_financial_kind_with_no_claims_declines() -> None:
    out = NumericRecomputationCheck().run(_model(None, kind=ArtifactKind.SLIDE_DECK))
    assert out == ()


# ---- determinism ---------------------------------------------------------------


def test_repeated_runs_are_identical() -> None:
    artifact = _model(
        (
            _claim("a", Decimal("10"), Decimal("10")),
            _claim("b", Decimal("21"), Decimal("20")),
        )
    )
    check = NumericRecomputationCheck()
    runs = [check.run(artifact) for _ in range(64)]
    first = runs[0]
    assert all(r == first for r in runs)
    assert len(first) == 1 and first[0].locator == "b"


# ---- property-based (hypothesis) -----------------------------------------------

# Money-shaped, bounded, 2-place Decimals: exact arithmetic well within the default
# 28-digit context, so an injected non-zero delta can never round back to equality.
_LABELS = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=1, max_size=24
)
_MONEY = st.decimals(
    min_value=Decimal("-1000000"),
    max_value=Decimal("1000000"),
    places=2,
    allow_nan=False,
    allow_infinity=False,
)
_NONZERO_DELTA = st.decimals(
    min_value=Decimal("-100000"),
    max_value=Decimal("100000"),
    places=2,
    allow_nan=False,
    allow_infinity=False,
).filter(lambda d: d != Decimal("0"))


@settings(max_examples=300, deadline=None)
@given(label=_LABELS, value=_MONEY)
def test_property_declared_equals_recomputed_always_passes(
    label: str, value: Decimal
) -> None:
    out = NumericRecomputationCheck().run(_model((_claim(label, value, value),)))
    assert out == ()


@settings(max_examples=300, deadline=None)
@given(label=_LABELS, recomputed=_MONEY, delta=_NONZERO_DELTA)
def test_property_injected_delta_always_fails_with_that_label(
    label: str, recomputed: Decimal, delta: Decimal
) -> None:
    declared = recomputed + delta
    assume(declared != recomputed)  # belt-and-braces; bounded 2-place arithmetic is exact
    out = NumericRecomputationCheck().run(
        _model((_claim(label, declared, recomputed),))
    )
    assert len(out) == 1
    f = out[0]
    assert f.severity is CheckSeverity.BLOCKING
    assert f.check_id is ReviewCheckId.NUMERIC_RECOMPUTE
    assert f.defect_class is DefectClass.MECHANICAL
    assert f.locator == label
    assert f.expected == f"recomputed={recomputed}"
    assert f.actual == f"declared={declared}"


@settings(max_examples=200, deadline=None)
@given(
    data=st.lists(
        st.tuples(_LABELS, _MONEY, _NONZERO_DELTA), min_size=1, max_size=8
    )
)
def test_property_finding_count_equals_mismatch_count(
    data: list[tuple[str, Decimal, Decimal]],
) -> None:
    # Metamorphic: with unique labels, the number of findings equals the number of
    # claims whose declared != recomputed, and locators are exactly those labels.
    seen: set[str] = set()
    claims: list[NumericClaim] = []
    wrong_labels: list[str] = []
    for i, (raw_label, recomputed, delta) in enumerate(data):
        label = f"{raw_label}#{i}"  # force uniqueness (contract forbids dup labels)
        seen.add(label)
        declared = recomputed + delta
        assume(declared != recomputed)
        claims.append(_claim(label, declared, recomputed))
        wrong_labels.append(label)
    out = NumericRecomputationCheck().run(_model(tuple(claims)))
    assert [f.locator for f in out] == wrong_labels


# ---- EXACT finding-message strings (kill string-literal mutants) ---------------
#
# mutmut wraps every string literal in XX...XX; a substring `in` check survives that.
# These pin the FULL message with `==` so a single mutated character fails the test.


def test_mismatch_message_is_exact_full_string() -> None:
    """A declared!=recomputed claim's message is the EXACT literal (``==``)."""
    (finding,) = NumericRecomputationCheck().run(
        _model((_claim("gm", Decimal("100"), Decimal("99")),))
    )
    assert finding.message == (
        "declared figure does not match independent recomputation (exact to the unit)"
    )
    assert finding.expected == "recomputed=99"
    assert finding.actual == "declared=100"


def test_absent_facts_message_is_exact_full_string() -> None:
    """The fail-closed message is the EXACT literal (``==``), not a substring match."""
    (finding,) = NumericRecomputationCheck().run(
        _model(None, ref="artifact#missing-facts")
    )
    assert finding.message == "numeric-claim facts absent — cannot verify"
    assert finding.locator == "artifact#missing-facts"
    assert finding.expected is None
    assert finding.actual is None
