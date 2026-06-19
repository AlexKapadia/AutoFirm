"""The PURE degraded-mode policy: per missing dependency, degrade vs converge vs fail-closed.

What this does
--------------
Implements :func:`decide_degraded_action` — a single, total, side-effect-free function that
maps a dependency's :class:`Criticality` and presence to exactly one
:class:`DegradedAction`. It is the codification of the B3 degraded-mode policy table
(docs/research/B3-resilient-bootstrap/idempotency-and-degraded-mode-spec.md §2.1):

* OPTIONAL dependency absent  -> ``DEGRADE_CAPABILITY``  (bulkhead-isolate that capability,
  audit, re-probe; the platform stays UP).
* SECURITY control absent     -> ``FAIL_CLOSED``         (refuse the dependent path; never
  silently degrade a security control to "off").
* REQUIRED dependency absent  -> ``FAIL_CLOSED``         (the platform cannot serve that path
  correctly; refuse it, report it — but still NOT a whole-platform hard block).
* Any criticality, present     -> ``PROCEED``            (the capability is available).

Why it exists / where it sits
-----------------------------
The composition root (:mod:`autofirm.runtime.platform_composition_root`) calls this at
bind time for every capability that has an external dependency, and the bootstrapper uses
the same rule for steps. Keeping it a pure function makes it exhaustively testable and
mutation-hardenable: the load-bearing invariant is that the function NEVER returns a
whole-platform block and NEVER opens a security path that should be closed.

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed for SECURITY/REQUIRED (§5.6):** a missing security or required dependency
  resolves to ``FAIL_CLOSED`` for THAT path — never ``PROCEED`` (would open an unsafe path)
  and never ``DEGRADE_CAPABILITY`` (would silently turn a control "off").
* **Bulkhead for OPTIONAL (§5.6, B3 source 07):** a missing optional dependency degrades
  ONLY its own capability; the platform stays up.
* **Never a whole-platform hard block:** there is deliberately no "halt the platform"
  outcome in :class:`DegradedAction`. The worst per-capability outcome is a fail-closed
  refusal of that one path.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from autofirm.bootstrap.bootstrap_step_contract import Criticality


class DegradedAction(Enum):
    """The single action the policy prescribes for one (dependency, criticality) pair.

    There is intentionally NO whole-platform-halt member: the policy can refuse a single
    path (fail-closed) or disable a single capability (degrade), but never block the whole
    platform (§5.6, B3 §2 "never a whole-platform hard block").
    """

    PROCEED = "proceed"  # dependency present -> bind the capability normally
    DEGRADE_CAPABILITY = "degrade_capability"  # OPTIONAL absent -> bulkhead-isolate that capability
    FAIL_CLOSED = "fail_closed"  # SECURITY/REQUIRED absent -> refuse that path; never silently off


@dataclass(frozen=True)
class DependencyStatus:
    """Whether one named external dependency is present, and how critical it is.

    Args:
        name: Stable, self-documenting dependency id (e.g. ``"provider:anthropic"``,
            ``"control:secret_scan"``, ``"analysis:matplotlib"``).
        criticality: REQUIRED | SECURITY | OPTIONAL — selects the fail mode.
        present: True iff the dependency is currently available (key set, gateway
            reachable, backend importable, control installed).
    """

    name: str
    criticality: Criticality
    present: bool


@dataclass(frozen=True)
class DegradedDecision:
    """The audited result of the policy: the action plus a PII-free, deterministic reason."""

    dependency_name: str
    action: DegradedAction
    reason: str


def decide_degraded_action(status: DependencyStatus) -> DegradedDecision:
    """Map a dependency status to exactly one :class:`DegradedAction` (pure, total).

    The whole correctness of degraded-mode rests on this function; it is mutation-critical
    (a mutant flipping a fail-closed branch to a hard-block or to proceed MUST be killed by
    the tests). The rules, in order:

    1. **Present** -> ``PROCEED`` (regardless of criticality; the capability is available).
    2. **Absent + OPTIONAL** -> ``DEGRADE_CAPABILITY`` (bulkhead-isolate; platform stays UP).
    3. **Absent + SECURITY or REQUIRED** -> ``FAIL_CLOSED`` (refuse that path; never open it,
       never silently disable a control, never block the whole platform).

    Args:
        status: The dependency's presence and criticality.

    Returns:
        The prescribed :class:`DegradedDecision` with a deterministic reason string.
    """
    if status.present:
        # The dependency is available -> bind the capability normally. This is the only
        # branch that lets a path run; absence never reaches it.
        return DegradedDecision(
            dependency_name=status.name,
            action=DegradedAction.PROCEED,
            reason="dependency_present",
        )
    if status.criticality is Criticality.OPTIONAL:
        # bulkhead (§5.6): an OPTIONAL dependency degrades ONLY its own capability; the
        # platform stays UP and the capability is re-probed to self-heal.
        return DegradedDecision(
            dependency_name=status.name,
            action=DegradedAction.DEGRADE_CAPABILITY,
            reason="optional_dependency_absent_capability_degraded",
        )
    # fail-closed (§5.6): a SECURITY or REQUIRED dependency that is absent refuses its
    # dependent path. It is NEVER degraded-to-off (a silent security hole) and NEVER opened
    # (PROCEED), and there is no whole-platform-block outcome to fall through to.
    return DegradedDecision(
        dependency_name=status.name,
        action=DegradedAction.FAIL_CLOSED,
        reason="critical_dependency_absent_path_refused",
    )
