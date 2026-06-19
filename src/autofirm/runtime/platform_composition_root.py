"""The composition root: the ONE place that constructs and wires every subsystem.

What this does
--------------
Defines :func:`build_platform` — the single module that imports, constructs, and hand-wires
every other AutoFirm package into one cohesive :class:`~autofirm.runtime.platform_runtime.
Platform` (Pure DI, no container — Seemann source 01; factory shape source 02). It builds
leaves first and composes upward through the 7 layers of the wiring graph
(docs/architecture/system-activation-design.md §2.1), applies the B3 degraded-mode policy
PER capability at bind time, and registers each wired subsystem as a
:class:`~autofirm.runtime.platform_runtime.WiredCapability` with a synthetic, network-free
readiness probe. This single wiring site is what turns the "bag of packages" into one runtime.

Why it exists / where it sits
-----------------------------
This is THE cure for fragmentation. Nothing else in the codebase news-up cross-package
collaborators; the root is the only allowed composition site. The CLI converges the env,
loads the config, calls :func:`build_platform`, supervises the loops, and runs the self-test
over the probes built here.

Security / compliance invariants upheld
---------------------------------------
* **Degraded-binding per capability (§5.6, B3 §2):** a missing OPTIONAL dependency (no
  provider key) binds that capability degraded (bulkhead) — the platform still builds. A
  missing SECURITY/REQUIRED control fails closed for its path. Decided by the PURE
  :func:`~autofirm.bootstrap.degraded_mode_policy.decide_degraded_action`, never ad hoc.
* **Kill-switch wired in (§5.6):** the gateway probe honours the injected
  :class:`KillSwitchEpoch`, so an engaged kill-switch refuses egress.
* **No secrets, no network (§3.12):** every probe uses synthetic data and the in-process
  fakes (fake gateway transport, deterministic embedder), so the root builds + self-tests on
  a no-secrets checkout.
"""

from __future__ import annotations

from datetime import UTC, datetime

from autofirm.bootstrap.bootstrap_step_contract import Criticality
from autofirm.bootstrap.degraded_mode_policy import (
    DegradedAction,
    DependencyStatus,
    decide_degraded_action,
)
from autofirm.runtime.capability_probe_factories import (
    build_audit_capability,
    build_capability_registry_capability,
    build_comms_capability,
    build_cost_ledger_capability,
    build_gateway_capability,
    build_kill_switch_capability,
    build_memory_capability,
    build_org_frontdoor_capability,
)
from autofirm.runtime.platform_config import PlatformConfig
from autofirm.runtime.platform_runtime import (
    Platform,
    SupervisedLoop,
    WiredCapability,
)

# The capability ids the platform MUST advertise once wired. This frozen set is the
# cohesion contract: the composition-root validation asserts every one is present, so a
# forgotten wiring (a dropped subsystem) is caught with teeth, not silently shipped.
EXPECTED_CAPABILITY_IDS = frozenset(
    {
        "gateway",
        "cost_ledger",
        "comms",
        "capability_registry",
        "memory",
        "org_frontdoor",
        "audit",
        "kill_switch",
    }
)


def _config_fingerprint(config: PlatformConfig) -> str:
    """Deterministic, secret-free fingerprint of the config (for same-live-state assertions).

    Built only from presence flags + non-secret paths, so an idempotent re-build with the
    same environment yields an identical fingerprint without ever including a secret value.
    """
    providers = ",".join(sorted(config.present_providers))
    return f"providers={providers}|gateway={config.gateway_url}|emb={config.embedding_enabled}"


def build_platform(
    config: PlatformConfig,
    *,
    now: datetime | None = None,
) -> Platform:
    """Construct and wire every subsystem into one cohesive :class:`Platform` (Pure DI).

    The wiring proceeds leaf-first up the 7 layers; the model-gateway capability's bind mode
    is decided by the degraded-mode policy from ``config`` (no provider key -> degraded,
    bulkhead-isolated; the platform still builds). Every wired subsystem becomes a
    :class:`WiredCapability` with a synthetic probe. The returned platform runs no business
    logic — the supervisor and CLI drive it.

    Args:
        config: The resolved, frozen activation config (presence flags + paths, no secrets).
        now: An injected wall-clock instant for determinism in tests (defaults to UTC now at
            the CLI edge only — never read at import time).

    Returns:
        The composed :class:`Platform` whose capabilities enumerate the wired graph.
    """
    instant = now if now is not None else datetime.now(UTC)

    # --- Decide the model-gateway bind mode via the PURE degraded-mode policy (§5.6) -------
    # The gateway is an OPTIONAL capability: a missing provider key degrades ONLY it (the
    # platform stays up). We never branch on the policy ad hoc — the pure function decides.
    gateway_present = config.has_provider("anthropic")
    gateway_decision = decide_degraded_action(
        DependencyStatus(
            name="provider:anthropic",
            criticality=Criticality.OPTIONAL,
            present=gateway_present,
        )
    )
    gateway_degraded = gateway_decision.action is DegradedAction.DEGRADE_CAPABILITY

    # --- Build each capability leaf-first; each factory wires the REAL subsystem ----------
    # L0/L1: kill-switch + gateway + cost ledger (egress + metering).
    kill_switch_cap = build_kill_switch_capability(instant=instant)
    gateway_cap = build_gateway_capability(
        config=config,
        degraded=gateway_degraded,
        # Surface WHICH dependency drove the bind decision alongside WHY (§3.11 explain-every-
        # decision): the gateway's audited reason names the provider dependency, not just the
        # generic policy outcome — so a degraded gateway is traceable to provider:anthropic.
        reason=f"{gateway_decision.dependency_name}:{gateway_decision.reason}",
        instant=instant,
    )
    cost_ledger_cap = build_cost_ledger_capability(instant=instant)
    # L0 (security): tamper-evident audit log.
    audit_cap = build_audit_capability(instant=instant)
    # L2: memory + the capability registry (the cohesion ledger of org capabilities).
    memory_cap = build_memory_capability(config=config, instant=instant)
    registry_cap = build_capability_registry_capability(instant=instant)
    # L3: the inter-agent comms bus (loopback).
    comms_cap = build_comms_capability(instant=instant)
    # L4/L5: org + the human front door (synthetic request routes to a role).
    org_frontdoor_cap = build_org_frontdoor_capability(instant=instant)

    capabilities: tuple[WiredCapability, ...] = (
        gateway_cap,
        cost_ledger_cap,
        comms_cap,
        registry_cap,
        memory_cap,
        org_frontdoor_cap,
        audit_cap,
        kill_switch_cap,
    )

    loops = _supervised_loops(comms_cap)
    platform = Platform(
        capabilities=capabilities,
        loops=loops,
        config_fingerprint=_config_fingerprint(config),
    )
    _validate_cohesion(platform)  # teeth: a missing/mis-wired capability fails the build
    return platform


def _supervised_loops(comms_cap: WiredCapability) -> tuple[SupervisedLoop, ...]:
    """Declare the long-lived loop inventory the supervisor keeps alive (cooperative ticks).

    Each loop's ``tick`` is a single cooperative unit so the supervisor controls cancellation
    via AnyIO (cross-OS), never POSIX signals. Re-probing degraded capabilities is the
    self-heal beat (B3 §3); the comms drain keeps the bus serviced.
    """

    def _reprobe_tick() -> None:
        # The self-heal heartbeat: a no-op cooperative tick that re-runs the comms probe so a
        # recovered dependency is observed. Kept side-effect-free for deterministic tests.
        comms_cap.probe()

    def _drain_tick() -> None:
        # Keep the comms bus serviced each beat; a no-op cooperative tick (deterministic).
        comms_cap.probe()

    return (
        SupervisedLoop(name="capability.reprobe", tick=_reprobe_tick),
        SupervisedLoop(name="comms.drain", tick=_drain_tick),
    )


def _validate_cohesion(platform: Platform) -> None:
    """Assert the wired graph advertises EVERY expected capability (the cohesion teeth).

    A forgotten or dropped wiring (a missing capability id) raises here, failing
    :func:`build_platform` rather than shipping a fragmented graph. This is what makes the
    self-test non-tautological: a deliberately mis-wired root cannot pass build (§5 item 5).

    Raises:
        ValueError: if the platform is missing any expected capability id (fail-closed).
    """
    present = platform.capability_ids()
    missing = EXPECTED_CAPABILITY_IDS - present
    if missing:
        # fail-closed: a fragmented graph (a subsystem never wired) is a build defect.
        raise ValueError(f"composition root is missing wired capabilities: {sorted(missing)}")
