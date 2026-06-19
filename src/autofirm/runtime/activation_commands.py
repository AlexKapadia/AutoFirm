"""The activation command logic: up / status / doctor / down as pure, typer-free functions.

What this does
--------------
Implements the behaviour behind the four CLI verbs as plain functions that take an injected
environment + a :class:`MappingEnvProbe` and return a typed
:class:`CommandResult` (exit code + a rendered summary). Keeping the logic here — free of
Typer — means the whole activation flow is unit-testable directly (and via the CLI runner),
and Typer/Click stay confined to :mod:`autofirm.runtime.cli_entrypoint` (import-linter
contract — design §7).

* ``up`` = converge the env (B3 bootstrapper) -> load config -> ``build_platform`` -> supervise
  -> run the readiness self-test. Idempotent; exits 0 unless a REQUIRED/SECURITY probe is RED.
* ``status`` = re-run the readiness self-test + report supervised-loop state.
* ``doctor`` = read-only ``check()`` of every bootstrap step (never ``apply()``).
* ``down`` = cooperative drain of the supervised loops.

Security / compliance invariants upheld
---------------------------------------
* **Never a whole-platform hard block (§5.6):** a missing OPTIONAL dependency degrades and
  ``up`` still exits 0; only a RED (REQUIRED/SECURITY) failure exits non-zero.
* **No secrets, no network (§3.12):** config records presence flags only; probes are synthetic.
* **Deterministic:** an injected instant + env mapping make every command reproducible.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from autofirm.bootstrap.bootstrap_doctor_report import diagnose
from autofirm.bootstrap.idempotent_environment_bootstrapper import (
    IdempotentEnvironmentBootstrapper,
)
from autofirm.runtime.activation_bootstrap_steps import MappingEnvProbe, activation_steps
from autofirm.runtime.platform_composition_root import build_platform
from autofirm.runtime.platform_config import PlatformConfig
from autofirm.runtime.platform_readiness_selftest import (
    ReadinessResult,
    run_readiness_selftest,
)
from autofirm.runtime.platform_supervisor import PlatformSupervisor

# Exit codes (12-Factor / B3 §1.3): 0 = acceptable (green or degraded); 1 = a required/
# security path is down (fail-closed). The CLI maps these straight to its process exit.
EXIT_OK = 0
EXIT_FAILED = 1
# How many supervision cycles `up` runs to prove the loops start and stay healthy. Bounded so
# the command is finite (no real never-ending process) yet long enough to exercise restarts.
_UP_SUPERVISION_CYCLES = 2


@dataclass(frozen=True)
class CommandResult:
    """A command's outcome: an exit code plus a deterministic, secret-free summary line."""

    exit_code: int
    summary: str

    @property
    def ok(self) -> bool:
        """True iff the command exited acceptably (exit code 0)."""
        return self.exit_code == EXIT_OK


def _instant(now: datetime | None) -> datetime:
    """Resolve the injected instant, defaulting to UTC now ONLY at the command edge."""
    return now if now is not None else datetime.now(UTC)


def run_up(
    environ: Mapping[str, str],
    *,
    env_probe: MappingEnvProbe,
    now: datetime | None = None,
) -> tuple[CommandResult, ReadinessResult]:
    """Converge the env, compose + supervise the platform, and run the readiness self-test.

    This is THE one flawless command. It is idempotent: a second call on a converged probe
    performs zero env mutations (the bootstrapper's ``check()`` gates every ``apply()``) and
    re-activates to the same live state. It NEVER hard-blocks on a missing OPTIONAL dependency
    (the gateway/memory degrade and ``up`` still exits 0); only a RED self-test exits 1.

    Returns:
        The :class:`CommandResult` (exit code + summary) and the full :class:`ReadinessResult`
        (so callers/tests can assert per-capability state).
    """
    instant = _instant(now)
    # 1. Converge the environment (B3 idempotent bootstrapper) — check() gates apply().
    bootstrapper = IdempotentEnvironmentBootstrapper(activation_steps())
    bootstrap_result = bootstrapper.converge(env_probe)
    # 2. Load the config ONCE from the environment (presence flags only, never secrets).
    config = PlatformConfig.from_environment(environ)
    # 3. Compose + wire the whole graph at the single composition root (degraded per cap).
    platform = build_platform(config, now=instant)
    # 4. Supervise the long-lived loops (bounded cycles here; the breaker keeps them honest).
    supervisor = PlatformSupervisor(platform)
    supervision = supervisor.run_cycles(_UP_SUPERVISION_CYCLES)
    # 5. Run the post-activation readiness self-test — proves the wired system serves.
    readiness = run_readiness_selftest(platform)
    exit_code = EXIT_OK if readiness.ok else EXIT_FAILED
    summary = (
        f"up: bootstrap mutations={bootstrap_result.mutations} "
        f"readiness={readiness.grade.value} loops_healthy={supervision.all_healthy} "
        f"capabilities={len(platform.capabilities)}"
    )
    return CommandResult(exit_code=exit_code, summary=summary), readiness


def run_status(
    environ: Mapping[str, str],
    *,
    now: datetime | None = None,
) -> tuple[CommandResult, ReadinessResult]:
    """Re-run the readiness self-test on a freshly-composed read-only platform (level-triggered).

    Mirrors a Kubernetes status read: it rebuilds the graph from the current environment and
    re-runs the probes, so it reports the live capability/loop state on demand without
    mutating anything.
    """
    instant = _instant(now)
    config = PlatformConfig.from_environment(environ)
    platform = build_platform(config, now=instant)
    readiness = run_readiness_selftest(platform)
    degraded = tuple(r.capability_id for r in readiness.reports if r.degraded)
    exit_code = EXIT_OK if readiness.ok else EXIT_FAILED
    summary = (
        f"status: readiness={readiness.grade.value} "
        f"capabilities={len(readiness.reports)} degraded={list(degraded)}"
    )
    return CommandResult(exit_code=exit_code, summary=summary), readiness


def run_doctor(*, env_probe: MappingEnvProbe) -> CommandResult:
    """Read-only diagnosis of every bootstrap step (``check()`` only — never ``apply()``).

    Reports exactly what is missing and how to fix it; exits 0 unless a REQUIRED/SECURITY
    step is FAILED (DEGRADED is allowed and reported). Mutates nothing (B3 §1.3).
    """
    report = diagnose(activation_steps(), env_probe)
    missing = tuple(f"{d.step_id}({d.state.value})" for d in report.missing)
    exit_code = EXIT_OK if report.ok else EXIT_FAILED
    summary = f"doctor: ok={report.ok} missing={list(missing)}"
    return CommandResult(exit_code=exit_code, summary=summary)


def run_down(
    environ: Mapping[str, str],
    *,
    now: datetime | None = None,
) -> CommandResult:
    """Cooperatively drain the supervised loops (graceful ``down`` — cross-OS, no signals).

    Composes the platform to obtain its loop inventory, then drains every healthy loop. The
    drain is cooperative (AnyIO-style), so it behaves identically on Windows and Linux.
    """
    instant = _instant(now)
    config = PlatformConfig.from_environment(environ)
    platform = build_platform(config, now=instant)
    supervisor = PlatformSupervisor(platform)
    snapshot = supervisor.drain()
    summary = f"down: drained loops={len(snapshot.loops)} all_healthy={snapshot.all_healthy}"
    return CommandResult(exit_code=EXIT_OK, summary=summary)
