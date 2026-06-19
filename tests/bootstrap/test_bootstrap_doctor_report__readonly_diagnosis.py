"""Tests for the read-only doctor report: reports missing deps, never mutates, fail-closed exit."""

from __future__ import annotations

from dataclasses import dataclass, field

from autofirm.bootstrap.bootstrap_doctor_report import diagnose
from autofirm.bootstrap.bootstrap_step_contract import Criticality, EnvProbe, StepState


@dataclass
class _Probe:
    facts: set[str] = field(default_factory=set)
    apply_calls: int = 0

    def has(self, key: str) -> bool:
        return key in self.facts

    def record(self, key: str) -> None:
        self.apply_calls += 1  # diagnose() must NEVER call this
        self.facts.add(key)


@dataclass(frozen=True)
class _Step:
    fact: str
    step_criticality: Criticality

    @property
    def id(self) -> str:
        return self.fact

    @property
    def requires(self) -> tuple[str, ...]:
        return ()

    @property
    def criticality(self) -> Criticality:
        return self.step_criticality

    def check(self, env: EnvProbe) -> bool:
        return env.has(self.fact)

    def apply(self, env: EnvProbe) -> None:  # pragma: no cover - doctor must never reach this
        env.record(self.fact)


def _steps() -> tuple[_Step, ...]:
    return (
        _Step("venv", Criticality.REQUIRED),
        _Step("plotting", Criticality.OPTIONAL),
        _Step("secret_scan", Criticality.SECURITY),
    )


def test_diagnose__is_read_only_never_calls_apply() -> None:
    """Doctor runs check() ONLY — apply() is never invoked, so it cannot mutate the env."""
    probe = _Probe()
    diagnose(_steps(), probe)
    assert probe.apply_calls == 0  # the read-only invariant (B3 §1.3)


def test_diagnose__all_satisfied_is_ok_with_no_missing() -> None:
    """When every step's check() passes, the report is ok and reports nothing missing."""
    probe = _Probe(facts={"venv", "plotting", "secret_scan"})
    report = diagnose(_steps(), probe)
    assert report.ok
    assert report.missing == ()


def test_diagnose__missing_security_step_is_failed_and_not_ok() -> None:
    """A missing SECURITY step is FAILED (fail-closed) and drives a non-ok (non-zero) report."""
    probe = _Probe(facts={"venv", "plotting"})  # secret_scan absent
    report = diagnose(_steps(), probe)
    assert not report.ok
    failed = [d for d in report.missing if d.step_id == "secret_scan"]
    assert failed and failed[0].state is StepState.FAILED


def test_diagnose__missing_optional_step_is_degraded_but_still_ok() -> None:
    """A missing OPTIONAL step is DEGRADED and reported, but does NOT make the report non-ok."""
    probe = _Probe(facts={"venv", "secret_scan"})  # plotting absent
    report = diagnose(_steps(), probe)
    assert report.ok  # degraded is allowed (platform stays UP)
    degraded = [d for d in report.missing if d.step_id == "plotting"]
    assert degraded and degraded[0].state is StepState.DEGRADED
    assert degraded[0].remediation  # a non-empty 'how to fix' hint


def test_diagnose__missing_required_step_carries_remediation_hint() -> None:
    """A missing REQUIRED step reports FAILED with an actionable remediation string."""
    report = diagnose(_steps(), _Probe())  # nothing satisfied
    venv = next(d for d in report.missing if d.step_id == "venv")
    assert venv.state is StepState.FAILED
    assert "autofirm up" in venv.remediation
