"""Charter validation tests: the JCM/MPS-collapse completeness gate, fail-closed.

Proves a :class:`RoleCharter` refuses every under-specified spec — the
no-spawn-without-a-complete-spec invariant at construction (A1.5 §2(2), [03]).
Boundary-exact: each forbidden field is emptied in isolation so the specific
guard that fires is unambiguous. Synthetic only; no network (CLAUDE.md §3.6/§5.5).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from autofirm.org.org_identifiers import ArtifactId, RoleId
from autofirm.org.role_charter_contract import ROOT_AUTHOR, RoleCharter


def _kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "role_id": RoleId("r"),
        "title": "Role",
        "responsibilities": ("do-the-thing",),
        "ownership_scope": "a-real-scope",
        "success_signal": "a-real-kpi",
        "owned_artifacts": frozenset({ArtifactId("a")}),
        "manager_id": RoleId("m"),
        "authored_by": RoleId("m"),
    }
    base.update(overrides)
    return base


@pytest.mark.unit
def test_a_complete_charter_constructs() -> None:
    charter = RoleCharter(**_kwargs())  # type: ignore[arg-type]
    assert charter.role_id == RoleId("r")
    assert not charter.is_root()


@pytest.mark.unit
@pytest.mark.parametrize("field", ["title", "ownership_scope", "success_signal"])
@pytest.mark.parametrize("blank", ["", "   ", "\t\n"])
def test_blank_required_text_is_refused(field: str, blank: str) -> None:
    # MPS-collapse gate: no autonomy (scope) or no feedback (signal) -> refused.
    with pytest.raises(ValidationError):
        RoleCharter(**_kwargs(**{field: blank}))  # type: ignore[arg-type]


@pytest.mark.unit
def test_empty_responsibilities_is_refused() -> None:
    # A role that does nothing is not a role (JCM variety/identity).
    with pytest.raises(ValidationError):
        RoleCharter(**_kwargs(responsibilities=()))  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.parametrize("bad", [("",), ("ok", "  "), ("\t",)])
def test_blank_responsibility_entry_is_refused(bad: tuple[str, ...]) -> None:
    with pytest.raises(ValidationError):
        RoleCharter(**_kwargs(responsibilities=bad))  # type: ignore[arg-type]


@pytest.mark.unit
def test_root_charter_is_root_and_non_root_is_not() -> None:
    root = RoleCharter(**_kwargs(manager_id=None, authored_by=ROOT_AUTHOR))  # type: ignore[arg-type]
    assert root.is_root()
    assert not RoleCharter(**_kwargs()).is_root()  # type: ignore[arg-type]


@pytest.mark.unit
def test_charter_is_frozen_immutable() -> None:
    charter = RoleCharter(**_kwargs())  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        charter.title = "mutated"  # type: ignore[misc]  # frozen — append-only authorship
