"""The code-vs-data boundary: sensitive data lives only in a gitignored .autofirm/ root.

What this does
--------------
Marks and enforces the boundary between the **code repo** (committed, deployable)
and the **sensitive workspace** (secrets, finance, company data) which must live
ONLY in a gitignored ``.autofirm/`` root and must NEVER be committed or deployed.

:class:`WorkspaceDataBoundary` resolves a sensitive path *under* the workspace root
and fails closed if a caller tries to:

* place sensitive data outside the ``.autofirm/`` root, or
* escape the root via ``..``/absolute-path traversal, or
* point the workspace root *inside* the code repo (which would risk committing it).

Why it exists / where it sits
-----------------------------
Research ``A6-governance-and-auditability/`` workspace-&-data-boundary line and the
project rule "public codebase separated from finance/sensitive data, never deployed
to GitHub". This module is the single, well-named gatekeeper that every component
routes sensitive-file paths through, so the separation is enforced in code rather
than left to discipline.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Fail closed:** any path that would resolve outside the workspace root, or a
  root that overlaps the code repo, is refused -- never silently relocated.
* **No traversal:** ``..`` / absolute components are rejected so a crafted relative
  path cannot escape the sensitive root.
* **Separation of secrets/data from code:** the boundary guarantees sensitive files
  resolve under ``.autofirm/`` and never under the repository tree.
"""

from __future__ import annotations

from pathlib import PurePosixPath

__all__ = ["SENSITIVE_WORKSPACE_DIRNAME", "WorkspaceDataBoundary", "WorkspaceBoundaryError"]

# The fixed, gitignored directory name that holds all sensitive workspace data.
# Committed .gitignore excludes it; this constant is the single source of truth.
SENSITIVE_WORKSPACE_DIRNAME = ".autofirm"


class WorkspaceBoundaryError(Exception):
    """Raised when a path would breach the code-vs-data boundary (fail-closed)."""


class WorkspaceDataBoundary:
    """Resolves sensitive paths under a gitignored ``.autofirm/`` root, fail-closed.

    Constructed with the absolute workspace root (which must end in
    :data:`SENSITIVE_WORKSPACE_DIRNAME`) and the absolute code-repo root it must NOT
    overlap. :meth:`resolve_sensitive_path` is the only way to obtain a path for
    sensitive data, and it refuses anything that would land outside the boundary.

    Paths are reasoned about as POSIX-style for deterministic, OS-independent
    boundary checks (the same relative path is judged identically on every host).
    """

    def __init__(self, workspace_root: str, code_repo_root: str) -> None:
        """Bind to the sensitive workspace root and the code repo it must not overlap."""
        root = PurePosixPath(workspace_root.replace("\\", "/"))
        repo = PurePosixPath(code_repo_root.replace("\\", "/"))
        # fail-closed: both anchors must be absolute so containment is unambiguous.
        if not root.is_absolute() or not repo.is_absolute():
            raise WorkspaceBoundaryError(
                "workspace_root and code_repo_root must be absolute paths"
            )
        # fail-closed: the sensitive root MUST be the dedicated gitignored dir, so
        # data can never be written into an arbitrary (committable) location.
        if root.name != SENSITIVE_WORKSPACE_DIRNAME:
            raise WorkspaceBoundaryError(
                f"workspace_root must end in '{SENSITIVE_WORKSPACE_DIRNAME}'"
            )
        # separation of code & data: the sensitive root must NOT sit inside the code
        # repo tree, or its contents could be staged/committed/deployed.
        if root == repo or _is_relative_to(root, repo):
            raise WorkspaceBoundaryError(
                "sensitive workspace root must live OUTSIDE the code repo"
            )
        self._root = root

    def resolve_sensitive_path(self, relative_path: str) -> str:
        """Return the absolute path for ``relative_path`` under the sensitive root.

        ``relative_path`` must be a relative path with no traversal; the result is
        guaranteed to live under the ``.autofirm/`` root. Refuses absolute paths and
        any ``..`` component so a crafted path cannot escape the boundary.

        Raises:
            WorkspaceBoundaryError: the path is absolute, empty, contains ``..``, or
                would otherwise resolve outside the sensitive root.
        """
        candidate = PurePosixPath(relative_path.replace("\\", "/"))
        # fail-closed: an absolute path ignores the root entirely -> refuse.
        if candidate.is_absolute():
            raise WorkspaceBoundaryError("sensitive path must be relative to the root")
        # fail-closed: empty path would resolve to the root itself, not a file.
        if not relative_path or not str(candidate).strip():
            raise WorkspaceBoundaryError("sensitive path must be non-empty")
        # no traversal: any '..' could climb out of the sensitive root -> refuse.
        if ".." in candidate.parts:
            raise WorkspaceBoundaryError("sensitive path must not contain '..'")
        resolved = self._root / candidate
        # Defence-in-depth: re-assert containment after joining (belt and braces).
        if not _is_relative_to(resolved, self._root):
            raise WorkspaceBoundaryError("resolved path escaped the sensitive root")
        return str(resolved)


def _is_relative_to(path: PurePosixPath, base: PurePosixPath) -> bool:
    """Return True iff ``path`` is ``base`` or sits beneath it (containment check)."""
    # PurePath.is_relative_to exists on 3.9+, but we re-implement against parts so
    # the check is explicit and a sibling like /a/bc is NOT judged inside /a/b.
    base_parts = base.parts
    path_parts = path.parts
    if len(path_parts) < len(base_parts):
        return False
    return path_parts[: len(base_parts)] == base_parts
