"""AutoFirm platform package — public, deployable orchestration core.

This is the runtime root for the AutoFirm platform (ADR-001 §6). It is
PUBLIC code only: no finance models, per-company data, or PII ever live here
(those belong under the gitignored ``.autofirm/`` workspace — see
``docs/architecture/ADR-002-repo-layout.md``). Analysis/plotting libraries are
fenced out of this closure by the import-linter contract (ADR-001 §5).
"""

__version__ = "0.0.1"
