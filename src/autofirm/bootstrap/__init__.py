"""Idempotent, self-healing environment bootstrap (B3) — the converge half of setup.

This package converges the *environment* to a desired baseline before the platform is
composed (see :mod:`autofirm.runtime`). It realises the B3 idempotency contract
(docs/research/B3-resilient-bootstrap/idempotency-and-degraded-mode-spec.md): every unit
of setup is a typed :class:`~autofirm.bootstrap.bootstrap_step_contract.BootstrapStep`
whose ``check()`` (a pure, side-effect-free predicate) GATES its ``apply()`` (forward-only,
re-entrant), so a re-run is a provable no-op. The
:class:`~autofirm.bootstrap.idempotent_environment_bootstrapper.IdempotentEnvironmentBootstrapper`
runs the steps in deterministic dependency order and is crash-safe (resume re-runs
``check()`` in order). The
:func:`~autofirm.bootstrap.degraded_mode_policy.decide_degraded_action` policy is PURE and
decides, per missing dependency criticality, whether to degrade that capability, converge
it, or fail closed — NEVER a whole-platform hard block (§5.6 fail-closed).

Where it sits: ``autofirm up`` calls this package first (converge the env), then hands off
to :mod:`autofirm.runtime` (compose + supervise + self-test). ``autofirm doctor`` calls only
the read-only diagnosis here.
"""

from __future__ import annotations

from autofirm.bootstrap.bootstrap_doctor_report import (
    BootstrapDoctorReport,
    StepDiagnosis,
    diagnose,
)
from autofirm.bootstrap.bootstrap_step_contract import (
    BootstrapStep,
    Criticality,
    EnvProbe,
    StepOutcome,
    StepState,
)
from autofirm.bootstrap.degraded_mode_policy import (
    DegradedAction,
    DependencyStatus,
    decide_degraded_action,
)
from autofirm.bootstrap.idempotent_environment_bootstrapper import (
    BootstrapResult,
    IdempotentEnvironmentBootstrapper,
)

__all__ = [
    "BootstrapDoctorReport",
    "BootstrapResult",
    "BootstrapStep",
    "Criticality",
    "DegradedAction",
    "DependencyStatus",
    "EnvProbe",
    "IdempotentEnvironmentBootstrapper",
    "StepDiagnosis",
    "StepOutcome",
    "StepState",
    "decide_degraded_action",
    "diagnose",
]
