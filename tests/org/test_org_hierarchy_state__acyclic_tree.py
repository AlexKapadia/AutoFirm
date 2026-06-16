"""Hierarchy-invariant tests: single-rooted, acyclic, no-orphan tree — fail-closed.

Proves :class:`OrgHierarchy` refuses every non-tree graph (0 or >1 roots, dangling
manager, reporting cycle) at construction, and that ``would_create_cycle`` is exact
on/just-over/just-under the loop boundary. A Hypothesis property test grows a tree
by arbitrary valid parent choices and asserts it always stays acyclic and
single-rooted. Synthetic only; no network (CLAUDE.md §3.6/§5.5).
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.org.org_hierarchy_state import HierarchyInvariantError, OrgHierarchy
from autofirm.org.org_identifiers import RoleId

from .synthetic_org_factory import charter, root_charter


def _tree(*charters: object) -> OrgHierarchy:
    return OrgHierarchy({c.role_id: c for c in charters})  # type: ignore[attr-defined]


@pytest.mark.unit
def test_single_root_tree_constructs() -> None:
    h = OrgHierarchy.with_root(root_charter("ceo"))
    assert h.root_id() == RoleId("ceo")
    assert h.role_ids() == {RoleId("ceo")}


@pytest.mark.unit
def test_zero_roots_is_refused() -> None:
    with pytest.raises(HierarchyInvariantError):
        _tree(charter("a", "b", "b"), charter("b", "a", "a"))  # mutual, no root


@pytest.mark.unit
def test_two_roots_is_refused() -> None:
    with pytest.raises(HierarchyInvariantError):
        _tree(root_charter("r1"), root_charter("r2"))  # forest, not a tree


@pytest.mark.unit
def test_dangling_manager_is_refused() -> None:
    with pytest.raises(HierarchyInvariantError):
        _tree(root_charter("ceo"), charter("x", "ghost", "ghost"))  # manager absent


@pytest.mark.unit
def test_direct_cycle_in_constructed_graph_is_refused() -> None:
    # A graph where a->b->a (plus a real root so the root-count guard passes) must
    # be refused by the acyclicity check itself, independent of the engine's
    # pre-emptive would_create_cycle guard.
    with pytest.raises(HierarchyInvariantError):
        _tree(
            root_charter("ceo"),
            charter("a", "b", "b"),  # a reports to b
            charter("b", "a", "a"),  # b reports to a -> cycle
        )


@pytest.mark.unit
def test_with_root_rejects_non_root_charter() -> None:
    with pytest.raises(HierarchyInvariantError):
        OrgHierarchy.with_root(charter("x", "m", "m"))  # has a manager -> not a root


@pytest.mark.unit
def test_direct_reports_and_add_remove() -> None:
    h = (
        OrgHierarchy.with_root(root_charter("ceo"))
        .with_role(charter("cfo", "ceo", "ceo"))
        .with_role(charter("fp", "cfo", "cfo"))
    )
    assert h.direct_reports(RoleId("ceo")) == {RoleId("cfo")}
    assert h.direct_reports(RoleId("cfo")) == {RoleId("fp")}
    # removing a manager with reports orphans them -> re-validation refuses it.
    with pytest.raises(HierarchyInvariantError):
        h.without_role(RoleId("cfo"))


@pytest.mark.unit
def test_would_create_cycle_boundary_exact() -> None:
    h = (
        OrgHierarchy.with_root(root_charter("ceo"))
        .with_role(charter("a", "ceo", "ceo"))
        .with_role(charter("b", "a", "a"))
    )
    # a -> b would loop (b is below a). just-over the line.
    assert h.would_create_cycle(RoleId("a"), RoleId("b")) is True
    # a -> a is a self-loop. on the line.
    assert h.would_create_cycle(RoleId("a"), RoleId("a")) is True
    # b -> ceo is fine (ceo is above). just-under the line.
    assert h.would_create_cycle(RoleId("b"), RoleId("ceo")) is False


@pytest.mark.property
@given(parents=st.lists(st.integers(min_value=0), min_size=0, max_size=30))
def test_growing_by_valid_parents_stays_a_tree(parents: list[int]) -> None:
    # Each new node i+1 reports to an EXISTING node (parents[i] mod count) -> the
    # graph is a tree by construction; the hierarchy must accept it and stay
    # single-rooted + acyclic for every prefix.
    h = OrgHierarchy.with_root(root_charter("n0"))
    existing = ["n0"]
    for i, raw in enumerate(parents):
        parent = existing[raw % len(existing)]
        child = f"n{i + 1}"
        h = h.with_role(charter(child, parent, parent))
        existing.append(child)
        assert h.root_id() == RoleId("n0")  # single root invariant
        assert len(h.role_ids()) == len(existing)  # acyclic accepted (no raise)
