"""The read-only ``doctor`` diagnosis: exactly what's missing and how to fix it.

What this does
--------------
Defines :func:`diagnose` — the read-only Monitor+Analyze surface of the bootstrap (B3
§1.3). It runs every step's ``check()`` ONLY (never ``apply()``) and reports, per step, its
id, criticality, the observed-vs-desired state, and a remediation hint. The aggregate
:class:`BootstrapDoctorReport` exposes ``ok`` (no step FAILED — DEGRADED is allowed) so the
CLI ``doctor`` verb can pick its exit code (B3 §1.3: 0 unless a required/security step is
FAILED).

Why it exists / where it sits
-----------------------------
This is the environment's self-knowledge surface — like ``kubectl get``. It NEVER mutates
anything, so a human (or the §4.8 watchdog) can ask "what's wrong?" with zero risk. It
shares the exact same steps the
:class:`~autofirm.bootstrap.idempotent_environment_bootstrapper.IdempotentEnvironmentBootstrapper`
converges, so doctor and up can never disagree about what "converged" means.

Security / compliance invariants upheld
---------------------------------------
* **Read-only (B3 §1.3):** only ``check()`` is called; ``apply()`` is never invoked here, so
  ``doctor`` cannot change the system it is diagnosing.
* **Fail-closed reporting (§5.6):** a SECURITY/REQUIRED step whose ``check()`` is False is
  reported FAILED (drives a non-zero exit), never quietly omitted.
"""

from __future__ import annotations

from dataclasses import dataclass

from autofirm.bootstrap.bootstrap_step_contract import (
    BootstrapStep,
    Criticality,
    EnvProbe,
    StepState,
)


@dataclass(frozen=True)
class StepDiagnosis:
    """One step's read-only diagnosis: id, criticality, observed state, and a fix hint."""

    step_id: str
    criticality: Criticality
    state: StepState
    remediation: str  # PII-free, deterministic 'how to fix' (empty when satisfied)


@dataclass(frozen=True)
class BootstrapDoctorReport:
    """The aggregate read-only report over every step (the ``doctor`` output)."""

    diagnoses: tuple[StepDiagnosis, ...]

    @property
    def ok(self) -> bool:
        """True iff no step is FAILED (DEGRADED is an allowed, reported state — B3 §1.3)."""
        return all(d.state is not StepState.FAILED for d in self.diagnoses)

    @property
    def missing(self) -> tuple[StepDiagnosis, ...]:
        """The subset of steps that are not SATISFIED (what is missing + how to fix it)."""
        return tuple(d for d in self.diagnoses if d.state is not StepState.SATISFIED)


def _diagnose_one(step: BootstrapStep, env: EnvProbe) -> StepDiagnosis:
    """Diagnose a single step read-only: SATISFIED if check() True, else DEGRADED/FAILED."""
    if step.check(env):
        return StepDiagnosis(
            step_id=step.id,
            criticality=step.criticality,
            state=StepState.SATISFIED,
            remediation="",
        )
    # Unsatisfied: an OPTIONAL gap degrades only its capability; a SECURITY/REQUIRED gap is
    # FAILED (fail-closed reporting -> non-zero doctor exit).
    if step.criticality is Criticality.OPTIONAL:
        return StepDiagnosis(
            step_id=step.id,
            criticality=step.criticality,
            state=StepState.DEGRADED,
            remediation=f"optional: install '{step.id}' to enable its capability",
        )
    return StepDiagnosis(
        step_id=step.id,
        criticality=step.criticality,
        state=StepState.FAILED,
        remediation=f"required: run 'autofirm up' (or fix '{step.id}') to converge it",
    )


def diagnose(steps: tuple[BootstrapStep, ...], env: EnvProbe) -> BootstrapDoctorReport:
    """Run every step's ``check()`` read-only and return the aggregate doctor report.

    Args:
        steps: The same bootstrap steps the bootstrapper converges (single source of truth).
        env: The read-only environment probe.

    Returns:
        A :class:`BootstrapDoctorReport` whose ``ok`` drives the ``doctor`` exit code.
    """
    return BootstrapDoctorReport(diagnoses=tuple(_diagnose_one(step, env) for step in steps))
