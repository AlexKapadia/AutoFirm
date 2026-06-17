"""Per-company isolated, deletable workspace + the injected data boundary.

Each validated company gets its OWN ``.autofirm/`` sensitive root nested under a
caller-supplied corpus directory (a test's ``tmp_path``), NEVER the real on-disk
``.autofirm/``. Everything a scenario writes — generated artifacts, filed
documents — lands under that root, so deleting the corpus directory removes the
whole company without touching the platform or any other company.

Security / isolation invariants (CLAUDE.md §3.12, §5.6)
------------------------------------------------------
* **Boundary-enforced separation:** the
  :class:`autofirm.access.workspace_data_boundary.WorkspaceDataBoundary` resolves
  every sensitive path under the per-company root and refuses any traversal — the
  same fail-closed primitive production uses, so the validation exercises the real
  guarantee rather than a stub.
* **Deletable by construction:** the root lives entirely under the corpus dir; the
  :meth:`IsolatedCompanyWorkspace.teardown` helper removes it and asserts it is
  gone, proving nothing leaked outside the deletable tree.
* **No overlap with the code repo:** the boundary refuses a root that sits inside
  the code repo, so a company workspace can never be one that would be committed.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from autofirm.access.workspace_data_boundary import (
    SENSITIVE_WORKSPACE_DIRNAME,
    WorkspaceDataBoundary,
)


@dataclass(frozen=True, slots=True)
class IsolatedCompanyWorkspace:
    """One company's isolated, deletable on-disk workspace and its data boundary.

    Args:
        company_slug: Slug-safe id; the company's folder name within the corpus.
        corpus_dir: The deletable parent directory holding every company (a test's
            ``tmp_path``). Removing it deletes the whole validation corpus.
        root_dir: The real ``.autofirm/`` sensitive root for this company.
        boundary: The fail-closed boundary that resolves paths under ``root_dir``.
    """

    company_slug: str
    corpus_dir: Path
    root_dir: Path
    boundary: WorkspaceDataBoundary

    def sensitive_dir(self, relative_path: str) -> Path:
        """Real, created OS dir for ``relative_path`` under the sensitive root.

        The relative path is first routed through the fail-closed boundary (which
        refuses traversal / escape and proves the location is under ``.autofirm/``),
        then mapped onto the real OS root so the artifact builders can write actual
        bytes. The boundary reasons in a POSIX-absolute mirror of the root; the
        real write uses ``root_dir`` — both point at the same logical location.
        """
        # fail-closed: the boundary refuses any path that would escape the root.
        self.boundary.resolve_sensitive_path(relative_path)
        resolved = self.root_dir / relative_path
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    def deliverables_dir(self) -> Path:
        """Real, created dir under the root where generated artifacts are written."""
        return self.sensitive_dir("deliverables")

    def teardown(self) -> None:
        """Delete this company's entire workspace; assert nothing remains.

        Proves deletability (CLAUDE.md §3.12): the root is removed recursively and
        its absence is asserted, so the validation demonstrates the corpus can be
        wiped without residue.
        """
        if self.root_dir.exists():
            shutil.rmtree(self.root_dir)
        # Deletability is a guarantee, not a hope: refuse to claim teardown if the
        # tree still exists (fail-closed on a silent leak).
        if self.root_dir.exists():  # pragma: no cover - defensive backstop
            raise RuntimeError(f"workspace teardown left residue at {self.root_dir}")


def create_isolated_company_workspace(
    *, company_slug: str, corpus_dir: Path
) -> IsolatedCompanyWorkspace:
    """Create a fresh, isolated, deletable workspace for one company.

    The sensitive root is ``<corpus_dir>/<company_slug>/.autofirm`` — fully nested
    under the deletable corpus dir and ending in the required gitignored dir name.
    A separate, non-overlapping ``code_repo`` anchor under the corpus dir satisfies
    the boundary's "data must live outside the code repo" invariant without ever
    touching the real repository.

    Args:
        company_slug: Slug-safe id; this company's folder within the corpus.
        corpus_dir: The deletable parent directory (a test's ``tmp_path``).

    Returns:
        A wired :class:`IsolatedCompanyWorkspace` whose boundary is the real
        fail-closed primitive bound to the per-company root.
    """
    company_dir = corpus_dir / company_slug
    root_dir = company_dir / SENSITIVE_WORKSPACE_DIRNAME
    code_repo_anchor = company_dir / "code_repo"  # non-overlapping sibling, never the real repo
    root_dir.mkdir(parents=True, exist_ok=True)

    # The boundary reasons over POSIX-absolute paths; convert the real OS paths so
    # the same primitive that guards production guards the validation too.
    boundary = WorkspaceDataBoundary(
        workspace_root=_as_posix_absolute(root_dir),
        code_repo_root=_as_posix_absolute(code_repo_anchor),
    )
    return IsolatedCompanyWorkspace(
        company_slug=company_slug,
        corpus_dir=corpus_dir,
        root_dir=root_dir,
        boundary=boundary,
    )


def _as_posix_absolute(path: Path) -> str:
    """Render a resolved OS path as a POSIX-ABSOLUTE mirror for the boundary.

    The boundary requires a POSIX-absolute root (one starting with ``/``). On
    Windows a resolved path is drive-prefixed (``C:/...``) which is NOT
    POSIX-absolute, so we prepend a single ``/`` to form a stable, unique mirror
    (``/C:/...``). This mirror is used ONLY by the boundary's path algebra (which
    does no filesystem I/O); the real reads/writes go through ``root_dir``. The
    company root and its code-repo anchor share the same parent, so the mirror
    preserves their non-overlap exactly as on disk.
    """
    forward = str(path.resolve()).replace("\\", "/")
    posix = PurePosixPath(forward)
    if posix.is_absolute():  # already POSIX-absolute (a real /-rooted path)
        return str(posix)
    return "/" + forward  # drive-prefixed Windows path -> stable /-rooted mirror
