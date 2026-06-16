"""Adversarial + property tests: sensitive paths resolve only under .autofirm/.

Proves the code-vs-data boundary fails closed: sensitive data resolves only under
the gitignored .autofirm/ root, traversal/absolute paths are refused, and a root
that overlaps the code repo is rejected so secrets/data can never be committed.
Synthetic paths only; no filesystem writes.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.access.workspace_data_boundary import (
    SENSITIVE_WORKSPACE_DIRNAME,
    WorkspaceBoundaryError,
    WorkspaceDataBoundary,
)

_WORKSPACE = f"/home/user/{SENSITIVE_WORKSPACE_DIRNAME}"
_REPO = "/home/user/AutoFirm"


def _boundary() -> WorkspaceDataBoundary:
    return WorkspaceDataBoundary(workspace_root=_WORKSPACE, code_repo_root=_REPO)


@pytest.mark.unit
def test_resolves_a_normal_sensitive_path_under_the_root() -> None:
    resolved = _boundary().resolve_sensitive_path("finance/acme/model.xlsx")
    assert resolved == f"{_WORKSPACE}/finance/acme/model.xlsx"
    assert resolved.startswith(_WORKSPACE + "/")


@pytest.mark.security
@pytest.mark.parametrize(
    "evil",
    [
        "../escape.txt",
        "finance/../../etc/passwd",
        "a/b/../../../outside",
        "..",
    ],
)
def test_traversal_paths_fail_closed(evil: str) -> None:
    # no traversal: any '..' could climb out of .autofirm/ -> refuse.
    with pytest.raises(WorkspaceBoundaryError):
        _boundary().resolve_sensitive_path(evil)


@pytest.mark.security
@pytest.mark.parametrize("absolute", ["/etc/passwd", "/home/user/AutoFirm/src/x.py"])
def test_absolute_paths_fail_closed(absolute: str) -> None:
    # fail-closed: an absolute path ignores the root entirely -> refuse.
    with pytest.raises(WorkspaceBoundaryError):
        _boundary().resolve_sensitive_path(absolute)


@pytest.mark.security
@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_path_fails_closed(blank: str) -> None:
    with pytest.raises(WorkspaceBoundaryError):
        _boundary().resolve_sensitive_path(blank)


@pytest.mark.security
def test_root_must_be_the_dedicated_gitignored_dir() -> None:
    # A root not named .autofirm/ could put data in a committable location -> refuse.
    with pytest.raises(WorkspaceBoundaryError):
        WorkspaceDataBoundary(workspace_root="/home/user/data", code_repo_root=_REPO)


@pytest.mark.security
def test_root_inside_the_code_repo_is_refused() -> None:
    # separation of code & data: a root under the repo could be committed -> refuse.
    inside = f"{_REPO}/{SENSITIVE_WORKSPACE_DIRNAME}"
    with pytest.raises(WorkspaceBoundaryError):
        WorkspaceDataBoundary(workspace_root=inside, code_repo_root=_REPO)


@pytest.mark.security
def test_relative_anchors_are_refused() -> None:
    with pytest.raises(WorkspaceBoundaryError):
        WorkspaceDataBoundary(workspace_root="relative/.autofirm", code_repo_root=_REPO)
    with pytest.raises(WorkspaceBoundaryError):
        WorkspaceDataBoundary(workspace_root=_WORKSPACE, code_repo_root="relative/repo")


@pytest.mark.unit
def test_sibling_dir_with_shared_prefix_is_not_inside_repo() -> None:
    # /home/user/AutoFirm-data shares a prefix with /home/user/AutoFirm but is NOT
    # inside it; a .autofirm root beside the repo must be accepted (no false block).
    sibling = "/home/user/AutoFirm-data/.autofirm"
    boundary = WorkspaceDataBoundary(workspace_root=sibling, code_repo_root=_REPO)
    assert boundary.resolve_sensitive_path("x").startswith(sibling + "/")


@pytest.mark.property
@given(
    segments=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=8,
        ),
        min_size=1,
        max_size=5,
    )
)
def test_property_clean_relative_paths_always_resolve_inside_root(
    segments: list[str],
) -> None:
    """Any traversal-free relative path resolves strictly under the .autofirm/ root."""
    relative = "/".join(segments)
    resolved = _boundary().resolve_sensitive_path(relative)
    # Containment holds for every clean path: the result starts at the root.
    assert resolved == f"{_WORKSPACE}/{relative}"
    assert resolved.startswith(_WORKSPACE + "/")
