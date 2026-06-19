"""The post-activation readiness self-test: run every capability probe, grade the result.

What this does
--------------
Defines :func:`run_readiness_selftest`, which runs the synthetic, network-free probe of
every wired capability on a :class:`~autofirm.runtime.platform_runtime.Platform` and grades
the platform GREEN / DEGRADED / RED. A REQUIRED or SECURITY probe failure is RED (the
platform is not serving); an OPTIONAL probe that reports degraded is DEGRADED but still
acceptable (the platform is UP — §5.6). This proves the WIRED system actually serves
end-to-end, not merely that objects were constructed (source 04, "ready to accept traffic").

Why it exists / where it sits
-----------------------------
``autofirm up`` runs this after the supervisor starts; ``autofirm status`` re-runs it on
demand. It is the teeth of the activation acceptance bar (§5 item 5): a deliberately
mis-wired graph fails it.

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed grading (§5.6):** a probe that RAISES (not just returns False) is treated as
  a failure, never swallowed; a SECURITY/REQUIRED failure makes the whole result RED.
* **Degraded is explicit (§5.6):** an OPTIONAL capability bound degraded is reported as
  DEGRADED with its reason, never silently dropped — and never makes the result RED.
* **Synthetic only (§3.12):** the probes use synthetic data, so the self-test runs on a
  no-secrets checkout with no network.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from autofirm.bootstrap.bootstrap_step_contract import Criticality
from autofirm.runtime.platform_runtime import Platform, WiredCapability


class ReadinessGrade(Enum):
    """The overall grade the self-test assigns the platform."""

    GREEN = "green"  # every probe passed (no degraded capabilities)
    DEGRADED = "degraded"  # all REQUIRED/SECURITY passed; some OPTIONAL degraded (platform UP)
    RED = "red"  # a REQUIRED or SECURITY probe FAILED (platform not serving — fail-closed)


@dataclass(frozen=True)
class ProbeReport:
    """One capability's probe result, graded: id, criticality, pass/fail, degraded, reason."""

    capability_id: str
    criticality: Criticality
    passed: bool
    degraded: bool
    reason: str


@dataclass(frozen=True)
class ReadinessResult:
    """The aggregate self-test result over every wired capability."""

    grade: ReadinessGrade
    reports: tuple[ProbeReport, ...]

    @property
    def ok(self) -> bool:
        """True iff the grade is acceptable for ``up`` to exit 0 (GREEN or DEGRADED)."""
        # DEGRADED is acceptable: an OPTIONAL capability being degraded NEVER hard-blocks the
        # platform (§5.6). Only RED (a REQUIRED/SECURITY failure) fails the gate.
        return self.grade is not ReadinessGrade.RED


def _run_one(capability: WiredCapability) -> ProbeReport:
    """Run a single capability probe, catching any raise as a fail-closed failure."""
    try:
        result = capability.probe()
        passed, reason = result.passed, result.reason
    except Exception as exc:
        # fail-closed: a probe that raises is a broken/un-served capability, graded as failed.
        passed, reason = False, f"probe_raised:{type(exc).__name__}"
    return ProbeReport(
        capability_id=capability.capability_id,
        criticality=capability.criticality,
        passed=passed,
        degraded=capability.degraded,
        reason=reason,
    )


def _grade(reports: tuple[ProbeReport, ...]) -> ReadinessGrade:
    """Grade the run: RED if any REQUIRED/SECURITY probe failed; else DEGRADED/GREEN.

    This is the load-bearing grading rule (mutation-critical): a failing REQUIRED or SECURITY
    probe MUST produce RED (a mutant that lets a broken subsystem grade GREEN must die). A
    failing OPTIONAL probe degrades but never makes the result RED (bulkhead §5.6).
    """
    for report in reports:
        if not report.passed and report.criticality is not Criticality.OPTIONAL:
            # A REQUIRED/SECURITY capability that did not pass means the platform is not
            # serving that essential/secure path -> RED (fail-closed), short-circuit.
            return ReadinessGrade.RED
    if any(r.degraded or not r.passed for r in reports):
        # Some OPTIONAL capability is degraded (or a failed-but-optional probe): the platform
        # is UP but running with a reduced capability set -> DEGRADED, not RED.
        return ReadinessGrade.DEGRADED
    return ReadinessGrade.GREEN


def run_readiness_selftest(platform: Platform) -> ReadinessResult:
    """Run every wired capability's probe and return the graded aggregate result.

    Args:
        platform: The composed platform whose capability probes are exercised.

    Returns:
        A :class:`ReadinessResult` whose ``grade`` and ``ok`` drive the CLI exit code.
    """
    reports = tuple(_run_one(capability) for capability in platform.capabilities)
    return ReadinessResult(grade=_grade(reports), reports=reports)
