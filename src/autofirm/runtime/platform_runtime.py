"""The composed Platform object: the wired object graph + the live capability ledger.

What this does
--------------
Defines the value types the composition root returns: a :class:`WiredCapability` (a named,
criticality-tagged subsystem with a synthetic *probe* closure that exercises the REAL wired
subsystem end-to-end), and the :class:`Platform` itself — the cohesive object graph. The
:class:`Platform` holds the wired subsystems, the live capability ledger, and the supervised
loop inventory; it carries NO business logic (Seemann separation — the root composes, the
supervisor/CLI run).

Why it exists / where it sits
-----------------------------
This object is the cure for fragmentation: instead of a bag of independently-constructed
packages, there is ONE :class:`Platform` whose :attr:`capabilities` enumerate every wired
subsystem and whose probes prove they actually serve. ``status`` renders this; the readiness
self-test runs the probes; the supervisor keeps the loops alive.

Security / compliance invariants upheld
---------------------------------------
* **Cohesion ledger:** every advertised subsystem MUST appear as a :class:`WiredCapability`,
  so a missing/forgotten wiring is detectable (the composition-root validation asserts the
  expected capability id set is present — its teeth).
* **Degraded is explicit, never silent (§5.6):** a capability bound in degraded mode carries
  ``degraded=True`` and a reason; nothing is quietly turned off.
* **Probes are synthetic (no network, no PII — §3.12):** each probe exercises its subsystem
  with synthetic data only, so the self-test runs on a no-secrets checkout.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from autofirm.bootstrap.bootstrap_step_contract import Criticality


@dataclass(frozen=True)
class ProbeResult:
    """The outcome of running one capability probe: passed/failed + a deterministic reason."""

    passed: bool
    reason: str


# A probe is a zero-argument closure that exercises the real wired subsystem with synthetic
# data and returns a :class:`ProbeResult`. It MUST NOT raise on a degraded capability (it
# reports ``passed=False`` with a reason); an unexpected raise is caught by the self-test and
# treated as a probe failure (fail-closed).
Probe = Callable[[], ProbeResult]


@dataclass(frozen=True)
class WiredCapability:
    """One wired subsystem registered in the cohesion ledger, with its readiness probe.

    Args:
        capability_id: Stable, self-documenting id (e.g. ``"gateway"``, ``"cost_ledger"``).
        criticality: REQUIRED | SECURITY | OPTIONAL — how a probe failure is graded.
        degraded: True iff the capability was bound in degraded mode (dependency absent).
        reason: PII-free 'why' for the degraded/bound state (audited, rendered by status).
        probe: A synthetic, network-free closure proving the subsystem serves end-to-end.
    """

    capability_id: str
    criticality: Criticality
    degraded: bool
    reason: str
    probe: Probe


@dataclass(frozen=True)
class SupervisedLoop:
    """One long-lived loop the supervisor owns: its name + a single cooperative tick.

    The platform declares its loop inventory here (heartbeats, comms drain, operate loop);
    the supervisor starts and keeps them alive. ``tick`` is a single cooperative unit of
    work so the supervisor controls cancellation (no POSIX signals — cross-OS, AnyIO).
    """

    name: str
    tick: Callable[[], None]


@dataclass(frozen=True)
class Platform:
    """The composed, wired object graph — one cohesive runtime, not a bag of packages.

    Args:
        capabilities: Every wired subsystem as a :class:`WiredCapability` (the cohesion
            ledger). ``status`` renders these; the self-test runs their probes.
        loops: The long-lived loop inventory the supervisor keeps alive.
        config_fingerprint: A deterministic, secret-free fingerprint of the config the graph
            was built from, so an idempotent re-build can assert "same live state".
    """

    capabilities: tuple[WiredCapability, ...]
    loops: tuple[SupervisedLoop, ...] = field(default_factory=tuple)
    config_fingerprint: str = ""

    def capability_ids(self) -> frozenset[str]:
        """Return the set of wired capability ids (used by the cohesion-ledger validation)."""
        return frozenset(c.capability_id for c in self.capabilities)

    def capability(self, capability_id: str) -> WiredCapability:
        """Return one wired capability by id (KeyError if absent — fail loud, never silent)."""
        for cap in self.capabilities:
            if cap.capability_id == capability_id:
                return cap
        # fail-closed: asking for a capability the platform does not advertise is a wiring
        # defect, surfaced loudly rather than returning a misleading default.
        raise KeyError(f"no wired capability {capability_id!r}")
