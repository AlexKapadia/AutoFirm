"""The typed ``BootstrapStep`` contract: a Burgess convergent operator as a protocol.

What this does
--------------
Defines the single unit of idempotent setup. Each step exposes two pure-intent methods —
``check()`` (a read-only, side-effect-free membership test for the desired state) and
``apply()`` (a forward-only, re-entrant convergence action) — plus DAG metadata
(``id``, ``requires``) and a :class:`Criticality` that selects its fail mode. This is a
Kubernetes-style reconcile step (B3 source 04) realising a Burgess convergent operator
(B3 source 01): ``check()`` GATES ``apply()`` so a re-run is a *provable* no-op, not an
accidental one.

Why it exists / where it sits
-----------------------------
This is the atom of :mod:`autofirm.bootstrap`. The
:class:`~autofirm.bootstrap.idempotent_environment_bootstrapper.IdempotentEnvironmentBootstrapper`
topologically orders steps by ``requires`` and runs the converge loop over them. The
contract is deliberately tiny and dependency-free so steps are trivially testable with a
synthetic :class:`EnvProbe`.

Security / compliance invariants upheld
---------------------------------------
* **check() gates apply() (B3 §1.2 clause 2):** the bootstrapper NEVER calls ``apply()``
  without ``check()`` first returning False. A guaranteed no-op on a converged tree is the
  whole point — accidental idempotence is forbidden.
* **Acceptance by predicate, not literal (§3.9 generality):** ``check()`` tests a property
  (e.g. "the venv import resolves"), never a magic fixture value, so the step is general.
* **Fail-closed criticality:** a SECURITY/REQUIRED step that cannot converge resolves to a
  named ``FAILED`` state, never a silent skip (§5.6).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable


class Criticality(Enum):
    """How a step's non-convergence is handled (selects the fail mode — B3 §2).

    REQUIRED and SECURITY steps fail CLOSED if they cannot converge (a named FAILED
    state, never a silent skip); OPTIONAL steps degrade only their own capability and
    leave the platform UP (bulkhead isolation — §5.6).
    """

    REQUIRED = "required"  # platform cannot serve correctly without it -> fail closed
    SECURITY = "security"  # a security/compliance control -> fail CLOSED, never degrade-to-off
    OPTIONAL = "optional"  # a single capability -> degrade only that capability, platform stays UP


class StepState(Enum):
    """The terminal state a step resolves to after the converge loop (B3 §1.1)."""

    SATISFIED = "satisfied"  # check() passed; apply() was a no-op this run
    APPLIED = "applied"  # apply() ran and converged the step this run
    DEGRADED = "degraded"  # capability unavailable; platform stays UP (OPTIONAL)
    FAILED = "failed"  # SECURITY/REQUIRED step could not converge -> fail closed


@runtime_checkable
class EnvProbe(Protocol):
    """Read-only window onto the live environment a step observes in ``check()``.

    Kept minimal and injectable so steps are deterministic in tests: a synthetic probe
    answers the membership questions without touching the real OS. ``has(key)`` reports
    whether a named environment fact holds (e.g. ``"venv.present"``); ``record(key)``
    marks a fact as now-true (the only mutation ``apply()`` performs in tests).
    """

    def has(self, key: str) -> bool:
        """Return True iff the named environment fact currently holds (side-effect-free)."""
        ...

    def record(self, key: str) -> None:
        """Mark the named environment fact as now-true (the apply() side effect)."""
        ...


@dataclass(frozen=True)
class StepOutcome:
    """The audited result of converging one step: its id, criticality, and final state."""

    step_id: str
    criticality: Criticality
    state: StepState
    detail: str  # PII-free, deterministic 'why' for the doctor/status surface


@runtime_checkable
class BootstrapStep(Protocol):
    """One typed unit of idempotent setup (a convergent operator — B3 §1.1).

    Implementations MUST honour: ``check()`` is read-only and side-effect-free; after a
    successful ``apply()``, ``check()`` returns True (the fixed-point property); and
    ``apply()`` is forward-only and re-entrant (safe to re-run after a crash mid-apply).
    """

    @property
    def id(self) -> str:
        """Stable, self-documenting step id (e.g. ``"venv.create"``)."""
        ...

    @property
    def requires(self) -> tuple[str, ...]:
        """Ids of steps that must be SATISFIED/APPLIED before this one (DAG edges)."""
        ...

    @property
    def criticality(self) -> Criticality:
        """The fail mode selector (REQUIRED | SECURITY | OPTIONAL)."""
        ...

    def check(self, env: EnvProbe) -> bool:
        """Membership test for the desired state. True => already converged => skip apply()."""
        ...

    def apply(self, env: EnvProbe) -> None:
        """Converge to the desired state. Forward-only, re-entrant; after it, check() is True."""
        ...
