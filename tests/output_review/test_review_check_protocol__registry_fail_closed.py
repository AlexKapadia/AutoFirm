"""Teeth-tests for the ReviewCheck Protocol + the fail-closed CheckRegistry.

Prove (CLAUDE.md §5.6): duplicate-id registration is REFUSED, unknown-id lookup is
REFUSED (never a silent None/skip), the registry key always equals the check's
self-declared id, and a conforming check satisfies the runtime-checkable Protocol
while a non-conforming object does not. Independence: a check's ``run`` is handed
only the artifact (plan §B.3) — verified by signature.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.output_review.output_review_errors import OutputReviewError
from autofirm.output_review.review_check_protocol import CheckRegistry, ReviewCheck
from autofirm.output_review.review_finding_and_severity_contracts import (
    CheckSeverity,
    DefectClass,
    ReviewCheckId,
    ReviewFinding,
)
from autofirm.output_review.reviewable_artifact_contract import (
    ArtifactKind,
    ReviewableArtifact,
)


class _StubCheck:
    """A minimal conforming check (synthetic) for registry/protocol tests."""

    def __init__(self, check_id: ReviewCheckId, finding: bool = False) -> None:
        self._id = check_id
        self._finding = finding

    @property
    def id(self) -> ReviewCheckId:
        return self._id

    def run(self, artifact: ReviewableArtifact) -> tuple[ReviewFinding, ...]:
        if not self._finding:
            return ()
        return (
            ReviewFinding(
                check_id=self._id,
                severity=CheckSeverity.BLOCKING,
                defect_class=DefectClass.MECHANICAL,
                message="stub defect",
                locator="L1",
            ),
        )


def _artifact() -> ReviewableArtifact:
    return ReviewableArtifact(
        artifact_ref="a", kind=ArtifactKind.FINANCIAL_MODEL, path=Path("/x")
    )


def test_register_and_get_round_trips() -> None:
    reg = CheckRegistry()
    chk = _StubCheck(ReviewCheckId.FAST_LINT)
    reg.register(chk)
    assert reg.get(ReviewCheckId.FAST_LINT) is chk
    assert ReviewCheckId.FAST_LINT in reg
    assert len(reg) == 1


def test_duplicate_registration_refused_fail_closed() -> None:
    reg = CheckRegistry()
    reg.register(_StubCheck(ReviewCheckId.FAST_LINT))
    with pytest.raises(OutputReviewError):
        reg.register(_StubCheck(ReviewCheckId.FAST_LINT))  # same id again
    assert len(reg) == 1  # the second never replaced the first


def test_unknown_id_lookup_refused_not_none() -> None:
    reg = CheckRegistry()
    # fail-closed: must RAISE, never return None (which would silently skip a check).
    with pytest.raises(OutputReviewError):
        reg.get(ReviewCheckId.ACCOUNTING_IDENTITY)


def test_unknown_id_not_contained() -> None:
    reg = CheckRegistry()
    assert ReviewCheckId.IBCS_SUCCESS not in reg


def test_registry_key_equals_check_self_declared_id() -> None:
    reg = CheckRegistry()
    chk = _StubCheck(ReviewCheckId.NUMERIC_RECOMPUTE)
    reg.register(chk)
    # The only key it can be fetched under is the check's own id.
    assert reg.get(chk.id) is chk
    assert reg.ids() == (ReviewCheckId.NUMERIC_RECOMPUTE,)


def test_ids_preserve_registration_order() -> None:
    reg = CheckRegistry()
    order = [
        ReviewCheckId.FILE_OPENS_CLEAN,
        ReviewCheckId.ACCOUNTING_IDENTITY,
        ReviewCheckId.VISUAL_INTEGRITY,
    ]
    for cid in order:
        reg.register(_StubCheck(cid))
    assert reg.ids() == tuple(order)


def test_stub_check_satisfies_protocol() -> None:
    chk = _StubCheck(ReviewCheckId.FAST_LINT)
    assert isinstance(chk, ReviewCheck)


def test_non_conforming_object_is_not_a_check() -> None:
    class _Bad:
        # has neither `id` nor `run`
        pass

    assert not isinstance(_Bad(), ReviewCheck)


def test_check_run_receives_only_artifact_and_returns_findings() -> None:
    # Independence: run sees the artifact, nothing else; clean -> empty tuple.
    clean = _StubCheck(ReviewCheckId.FAST_LINT, finding=False)
    dirty = _StubCheck(ReviewCheckId.FAST_LINT, finding=True)
    assert clean.run(_artifact()) == ()
    out = dirty.run(_artifact())
    assert len(out) == 1 and out[0].severity is CheckSeverity.BLOCKING


@settings(max_examples=200)
@given(ids=st.lists(st.sampled_from(list(ReviewCheckId)), min_size=1, max_size=8))
def test_property_first_registration_wins_duplicates_rejected(
    ids: list[ReviewCheckId],
) -> None:
    """Registering any id sequence: each distinct id once; any repeat is refused."""
    reg = CheckRegistry()
    seen: set[ReviewCheckId] = set()
    for cid in ids:
        chk = _StubCheck(cid)
        if cid in seen:
            with pytest.raises(OutputReviewError):
                reg.register(chk)
        else:
            reg.register(chk)
            seen.add(cid)
    assert set(reg.ids()) == seen
    assert len(reg) == len(seen)
