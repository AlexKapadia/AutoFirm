"""The externalized, re-grounded saga state passed at a handoff or resume.

What this does
--------------
Defines :class:`RegroundedSagaState` — the immutable bundle of state a session
externalizes so a successor (after a context handoff) or a relaunch (after a
failure) can *re-ground* on it rather than re-infer its purpose from a drifted
transcript. It is the caller-supplied half of a
:class:`~autofirm.substrate.context_handoff_summary.ContextHandoffSummary`
(the other half — ids, role, working dir, credential reference, fresh budget — is
copied off the session itself).

Its fields mirror A3 SYNTHESIS L1.A3.3's checkpoint data contract:

* ``goal_verbatim`` — the goal stored ONCE and re-injected unchanged (defends
  against goal misgeneralization / silent drift, A3 src 07).
* ``application_state`` (SA) — git ref / working-dir markers: where the work is.
* ``operation_state`` (SO) — the saga step + decision reasoning so far.
* ``dependency_state`` (SD) — outstanding dependencies / compensation metadata.
* ``work_complete`` — the explicit completeness signal the fail-closed resume
  gate consults (an ambiguous resume is refused, never inferred).

Why it exists / where it sits
-----------------------------
Bundling these five fields into one typed value object (rather than passing them
as five loose keyword arguments through every lifecycle method) keeps the engine
API small, gives the re-grounded state a single validated home, and makes "the
state we carry across a handoff" one auditable thing. It carries NO secret.

Security / compliance invariants upheld (CLAUDE.md §3.6, §5.6)
-------------------------------------------------------------
* **Re-ground, don't re-infer (A3):** ``goal_verbatim`` is required non-empty; a
  handoff/resume with no stored goal is refused at construction.
* **Fail-closed completeness signal (§5.6):** ``work_complete`` is an explicit
  boolean; the resume gate trusts it and refuses on ambiguity.
* **Secret-free:** there is no secret field on this object by construction.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = ["RegroundedSagaState"]


class RegroundedSagaState(BaseModel):
    """Immutable externalized state a successor/relaunch re-grounds on (no secret)."""

    model_config = ConfigDict(frozen=True)

    goal_verbatim: str  # stored ONCE, re-injected unchanged (anti-drift, A3 src 07)
    application_state: str  # SA: git ref / working-dir markers (where the work is)
    operation_state: str  # SO: saga step + decision reasoning so far
    dependency_state: str  # SD: outstanding deps + compensation metadata
    work_complete: bool  # the authority the fail-closed resume gate consults

    @field_validator("goal_verbatim")
    @classmethod
    def _goal_non_empty(cls, value: str) -> str:
        # fail-closed: a handoff/resume with no verbatim goal cannot re-ground a
        # successor -> refuse it, defending against goal drift (A3 src 07).
        if not value or not value.strip():
            raise ValueError("goal_verbatim must be non-empty (re-grounding requires it)")
        return value
