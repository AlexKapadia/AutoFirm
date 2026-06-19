"""Mutation-hardening tests for the BootstrapStep contract: enum wire values + protocol shape.

The contract module (:mod:`autofirm.bootstrap.bootstrap_step_contract`) is exercised only
indirectly by the bootstrapper/doctor suites, which left a large block of mutants alive: the
:class:`Criticality`/:class:`StepState` enum *values* (audit/wire strings), the
``@runtime_checkable`` protocol decorators, the ``frozen=True`` on :class:`StepOutcome`, and
the ``@property`` shape of the :class:`BootstrapStep` accessors. Each test below pins one of
those load-bearing facts so a mutant that corrupts it is killed (CLAUDE.md §3.6). None are
tautological — every assertion encodes a real consumer-visible contract.
"""

from __future__ import annotations

import dataclasses
import inspect

import pytest

from autofirm.bootstrap.bootstrap_step_contract import (
    BootstrapStep,
    Criticality,
    EnvProbe,
    StepOutcome,
    StepState,
)


def test_criticality__wire_values_are_pinned_exactly() -> None:
    """Each Criticality value is the EXACT audit/wire string (kills value-mutating mutants).

    These strings are serialised into the doctor/status surface and degraded-mode audit; a
    mutant that blanks or wraps one would silently corrupt that record, so each is literal.
    """
    assert Criticality.REQUIRED.value == "required"
    assert Criticality.SECURITY.value == "security"
    assert Criticality.OPTIONAL.value == "optional"
    # The member set is closed: exactly these three fail-mode selectors, no more, no fewer.
    assert {c.name for c in Criticality} == {"REQUIRED", "SECURITY", "OPTIONAL"}
    assert {c.value for c in Criticality} == {"required", "security", "optional"}


def test_step_state__wire_values_are_pinned_exactly() -> None:
    """Each StepState value is the EXACT terminal-state string (kills value-mutating mutants)."""
    assert StepState.SATISFIED.value == "satisfied"
    assert StepState.APPLIED.value == "applied"
    assert StepState.DEGRADED.value == "degraded"
    assert StepState.FAILED.value == "failed"
    assert {s.name for s in StepState} == {"SATISFIED", "APPLIED", "DEGRADED", "FAILED"}
    assert {s.value for s in StepState} == {"satisfied", "applied", "degraded", "failed"}


class _ConformingProbe:
    """A structural EnvProbe implementation (has + record)."""

    def has(self, key: str) -> bool:
        return False

    def record(self, key: str) -> None:
        return None


class _ConformingStep:
    """A structural BootstrapStep implementation (id/requires/criticality/check/apply)."""

    @property
    def id(self) -> str:
        return "s"

    @property
    def requires(self) -> tuple[str, ...]:
        return ()

    @property
    def criticality(self) -> Criticality:
        return Criticality.OPTIONAL

    def check(self, env: EnvProbe) -> bool:
        return True

    def apply(self, env: EnvProbe) -> None:
        return None


class _NotAProbe:
    """Missing ``record`` — must NOT be accepted as an EnvProbe."""

    def has(self, key: str) -> bool:
        return False


def test_env_probe__is_runtime_checkable_and_structurally_enforced() -> None:
    """EnvProbe stays ``@runtime_checkable`` AND checks structure (kills the decorator mutant).

    Removing ``@runtime_checkable`` makes ``isinstance(x, EnvProbe)`` raise ``TypeError`` (a
    non-runtime protocol cannot be used with isinstance) — so this test would error, killing
    the mutant. The negative case also proves the check is structural, not vacuous.
    """
    assert isinstance(_ConformingProbe(), EnvProbe)
    assert not isinstance(_NotAProbe(), EnvProbe)  # missing record() -> not a probe


def test_bootstrap_step__is_runtime_checkable_and_structurally_enforced() -> None:
    """BootstrapStep stays ``@runtime_checkable`` and enforces its full structural surface."""
    assert isinstance(_ConformingStep(), BootstrapStep)
    assert not isinstance(_ConformingProbe(), BootstrapStep)  # probe lacks id/requires/...


def test_step_outcome__is_frozen_immutable() -> None:
    """StepOutcome is an immutable audit record (kills the ``frozen=True`` -> False mutant)."""
    outcome = StepOutcome(
        step_id="venv.create",
        criticality=Criticality.REQUIRED,
        state=StepState.APPLIED,
        detail="converged_this_run",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.state = StepState.FAILED  # type: ignore[misc]


def test_step_outcome__carries_all_four_audit_fields_faithfully() -> None:
    """StepOutcome threads id/criticality/state/detail through unchanged (audit linkage)."""
    outcome = StepOutcome(
        step_id="control:secret_scan",
        criticality=Criticality.SECURITY,
        state=StepState.FAILED,
        detail="critical_step_unconverged_failed_closed",
    )
    assert outcome.step_id == "control:secret_scan"
    assert outcome.criticality is Criticality.SECURITY
    assert outcome.state is StepState.FAILED
    assert outcome.detail == "critical_step_unconverged_failed_closed"


@pytest.mark.parametrize("accessor", ["id", "requires", "criticality"])
def test_bootstrap_step__accessors_are_declared_as_properties(accessor: str) -> None:
    """The BootstrapStep DAG accessors are ``@property`` (kills the decorator-removal mutant).

    Consumers read ``step.id`` / ``step.requires`` / ``step.criticality`` as attributes; the
    contract declares them as properties to encode that attribute-style access. ``getattr_static``
    inspects the declaration without invoking it, so a removed ``@property`` (which turns the
    member into a plain function) is detected here.
    """
    declared = inspect.getattr_static(BootstrapStep, accessor)
    assert isinstance(declared, property)
