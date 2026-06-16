"""Gap-signal validation tests: a malformed gap cannot drive a spawn — fail-closed.

Proves :class:`OrgGap` refuses an empty rationale or a non-positive severity (a
malformed gap is not a gap), so automatic role-creation can never be triggered by
junk. Boundary-exact on severity. Synthetic only; no network.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from autofirm.org.gap_detection_contract import GapKind, OrgGap
from autofirm.org.org_identifiers import RoleId


@pytest.mark.unit
@pytest.mark.parametrize("kind", list(GapKind))
def test_valid_gap_of_every_kind_constructs(kind: GapKind) -> None:
    gap = OrgGap(kind=kind, detected_by=RoleId("m"), rationale="real reason", severity=1)
    assert gap.kind is kind
    assert gap.detected_by == RoleId("m")


@pytest.mark.unit
@pytest.mark.parametrize("blank", ["", "   ", "\n\t"])
def test_blank_rationale_is_refused(blank: str) -> None:
    with pytest.raises(ValidationError):
        OrgGap(kind=GapKind.SHORTAGE, detected_by=RoleId("m"), rationale=blank, severity=1)


@pytest.mark.unit
@pytest.mark.parametrize("sev", [0, -1, -100])
def test_non_positive_severity_is_refused(sev: int) -> None:
    # boundary: 0 is just-under the > 0 cutoff and must be refused.
    with pytest.raises(ValidationError):
        OrgGap(kind=GapKind.SHORTAGE, detected_by=RoleId("m"), rationale="r", severity=sev)


@pytest.mark.unit
def test_severity_one_is_just_accepted() -> None:
    gap = OrgGap(kind=GapKind.SKILL_GAP, detected_by=RoleId("m"), rationale="r", severity=1)
    assert gap.severity == 1


@pytest.mark.unit
def test_gap_is_frozen() -> None:
    gap = OrgGap(kind=GapKind.SHORTAGE, detected_by=RoleId("m"), rationale="r", severity=2)
    with pytest.raises(ValidationError):
        gap.severity = 9  # type: ignore[misc]  # immutable audit record
