"""Tests for the read-only doctor report: reports missing deps, never mutates, fail-closed exit."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field

import pytest

from autofirm.bootstrap.bootstrap_doctor_report import (
    StepDiagnosis,
    diagnose,
)
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


# ---------------------------------------------------------------------------
# Mutation-hardening (CLAUDE.md §3.6): pin the frozen-report invariants and the
# EXACT remediation strings (the substring/truthy checks above survive a string-
# wrapping mutant; an exact assertion kills it).
# ---------------------------------------------------------------------------


def test_step_diagnosis__is_frozen_immutable() -> None:
    """A StepDiagnosis is an immutable read-only record (kills the ``frozen=True`` mutant)."""
    diagnosis = StepDiagnosis(
        step_id="venv",
        criticality=Criticality.REQUIRED,
        state=StepState.FAILED,
        remediation="x",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        diagnosis.state = StepState.SATISFIED  # type: ignore[misc]


def test_doctor_report__is_frozen_immutable() -> None:
    """A BootstrapDoctorReport is frozen so a rendered diagnosis cannot be rewritten."""
    report = diagnose(_steps(), _Probe(facts={"venv", "plotting", "secret_scan"}))
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.diagnoses = ()  # type: ignore[misc]


def test_diagnose__satisfied_step_has_empty_remediation() -> None:
    """A SATISFIED step carries an EMPTY remediation (kills the ``""`` -> non-empty mutant)."""
    report = diagnose(_steps(), _Probe(facts={"venv", "plotting", "secret_scan"}))
    assert {d.state for d in report.diagnoses} == {StepState.SATISFIED}
    assert all(d.remediation == "" for d in report.diagnoses)


def test_diagnose__optional_remediation_string_is_byte_exact() -> None:
    """The OPTIONAL remediation hint is pinned EXACTLY (kills the f-string-wrap mutant)."""
    report = diagnose(_steps(), _Probe(facts={"venv", "secret_scan"}))  # plotting absent
    plotting = next(d for d in report.missing if d.step_id == "plotting")
    assert plotting.remediation == "optional: install 'plotting' to enable its capability"


def test_diagnose__required_remediation_string_is_byte_exact() -> None:
    """The REQUIRED remediation hint is pinned EXACTLY (kills the f-string-wrap mutant)."""
    report = diagnose(_steps(), _Probe())  # nothing satisfied
    venv = next(d for d in report.missing if d.step_id == "venv")
    assert venv.remediation == "required: run 'autofirm up' (or fix 'venv') to converge it"
