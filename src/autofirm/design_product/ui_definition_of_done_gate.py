"""The UI Definition-of-Done gate: DONE iff EVERY §4.9.7 quality gate passes.

What this does
--------------
Encodes CLAUDE.md §4.9.7's UI Definition-of-Done as a typed, evaluable contract.
:class:`UiDefinitionOfDoneGate` collects one :class:`GateResult` per required
quality gate (live E2E green, WCAG 2.2 AA, responsive, Core Web Vitals budget,
token adherence, state coverage, cross-browser, nothing-static) and
:meth:`evaluate` returns :data:`DoneVerdict.DONE` **only** when ALL required
gates are present AND every one passed. Any missing or failing gate yields
:data:`DoneVerdict.NOT_DONE` with the exact blocking reasons — fail-closed.

Why it exists / where it sits
-----------------------------
This is the acceptance mechanism the design workflow's VISUAL_REVIEW stage
consults before it may transition to DONE
(:mod:`~autofirm.design_product.design_workflow_state_machine`). It is the
"two-number quality gate, both CI-enforced" of SYNTHESIS §3 generalised to the
full §4.9.7 checklist. It is general — the same gate applies to any client UI.

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed (CLAUDE.md §5.6 / §4.9.7):** the default verdict is NOT_DONE. A
  candidate is DONE only on the AND of every required gate passing — an unknown,
  missing, or unevaluated gate blocks DONE, it never defaults to pass.
* **Complete coverage:** a result set missing any of :data:`REQUIRED_GATES` is
  refused as NOT_DONE (you cannot ship by simply omitting the gate you would
  fail).
* **Deterministic:** the verdict is a pure function of the supplied results — no
  ambient state, no clock — so the same evidence always yields the same verdict
  and the property tests can assert "DONE iff all pass" over arbitrary inputs.
* **Explained verdict (§3.11):** NOT_DONE always carries the specific blocking
  gates and their reasons; the "why" matches the "what" exactly.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

__all__ = [
    "REQUIRED_GATES",
    "DoneVerdict",
    "GateResult",
    "QualityGate",
    "UiDefinitionOfDoneGate",
    "UiDoneEvaluation",
]


class QualityGate(StrEnum):
    """The exhaustive set of UI Definition-of-Done gates (CLAUDE.md §4.9.7).

    Every one of these must pass for a UI to be "done"; they are the live-app
    acceptance checks, not code-only tests.
    """

    LIVE_E2E_GREEN = "LIVE_E2E_GREEN"  # Playwright drives the running app, all green
    WCAG_2_2_AA = "WCAG_2_2_AA"  # accessibility: automated + manual
    RESPONSIVE = "RESPONSIVE"  # correct at every breakpoint
    CORE_WEB_VITALS = "CORE_WEB_VITALS"  # LCP<=2.5s / CLS<=0.1 / INP<=200ms @p75
    TOKEN_ADHERENCE = "TOKEN_ADHERENCE"  # no hard-coded values (lint)
    STATE_COVERAGE = "STATE_COVERAGE"  # loading/empty/error/edge all present
    CROSS_BROWSER = "CROSS_BROWSER"  # works across target browsers
    NOTHING_STATIC = "NOTHING_STATIC"  # every control wired to real behaviour


# The closed set of gates that must ALL pass for DONE. A result set missing any of
# these is NOT_DONE by construction — you cannot ship by omitting a gate.
REQUIRED_GATES: frozenset[QualityGate] = frozenset(QualityGate)


class DoneVerdict(StrEnum):
    """The Definition-of-Done verdict: DONE only on the AND of every gate."""

    DONE = "DONE"  # every required gate present and passing — shippable
    NOT_DONE = "NOT_DONE"  # any gate missing or failing — fail-closed default


class GateResult(BaseModel):
    """One quality gate's outcome plus the evidence reason for that outcome.

    A passing result still carries a reason (the evidence locator), so the audit
    trail can show *why* a gate was judged green, not merely that it was.
    """

    model_config = ConfigDict(frozen=True)

    gate: QualityGate  # which §4.9.7 gate this result is for
    passed: bool  # did this gate pass on the live candidate?
    reason: str  # evidence / failure detail (non-empty, explains the outcome)

    @field_validator("reason")
    @classmethod
    def _reason_non_empty(cls, value: str) -> str:
        # fail-closed (§3.11 explain-every-decision): a gate outcome with no
        # evidence cannot be trusted or audited. Refuse a blank reason.
        if not value.strip():
            raise ValueError("gate result reason must be non-empty (evidence required)")
        return value


class UiDoneEvaluation(BaseModel):
    """The deterministic, explained outcome of evaluating the DoD gate.

    ``verdict`` is DONE only when ``blocking_gates`` is empty; otherwise every
    blocking gate (missing or failed) is named, so the "why" matches the "what".
    """

    model_config = ConfigDict(frozen=True)

    verdict: DoneVerdict
    blocking_gates: tuple[QualityGate, ...]  # missing or failed gates (empty iff DONE)
    blocking_reasons: tuple[str, ...]  # human-readable reason per blocking gate

    @model_validator(mode="after")
    def _verdict_matches_blockers(self) -> UiDoneEvaluation:
        # fail-closed self-consistency: DONE is permitted ONLY with zero blockers,
        # and NOT_DONE ONLY with at least one — so a DONE verdict can never be
        # constructed alongside a blocking gate (§3.11 why-matches-what).
        has_blockers = bool(self.blocking_gates)
        if (self.verdict is DoneVerdict.DONE) == has_blockers:
            raise ValueError("verdict must be DONE iff there are zero blocking gates")
        if len(self.blocking_gates) != len(self.blocking_reasons):
            raise ValueError("each blocking gate must carry exactly one reason")
        return self


class UiDefinitionOfDoneGate(BaseModel):
    """The typed §4.9.7 UI Definition-of-Done gate over a set of gate results.

    Construction refuses a duplicate result for the same gate (an ambiguous
    outcome). :meth:`evaluate` then returns DONE only on the AND of every required
    gate being present and passing — fail-closed on anything missing or failing.
    """

    model_config = ConfigDict(frozen=True)

    results: tuple[GateResult, ...]

    @field_validator("results")
    @classmethod
    def _no_duplicate_gate(cls, value: tuple[GateResult, ...]) -> tuple[GateResult, ...]:
        # fail-closed: two results for one gate (e.g. one pass, one fail) make the
        # verdict ambiguous and gameable. Refuse duplicates at construction.
        gates = [result.gate for result in value]
        if len(set(gates)) != len(gates):
            raise ValueError("duplicate result for a single gate (ambiguous outcome)")
        return value

    def evaluate(self) -> UiDoneEvaluation:
        """Return DONE iff every required gate is present AND passed (fail-closed).

        A gate is "blocking" if it is **missing** from ``results`` (you cannot ship
        by omitting it) or **present and failed**. The verdict is DONE only when
        there are zero blocking gates; otherwise NOT_DONE, naming each blocker and
        its reason so the refusal is fully explained (§3.11).
        """
        outcome_by_gate = {result.gate: result for result in self.results}
        blocking: list[tuple[QualityGate, str]] = []
        # Iterate the REQUIRED set, not the supplied results: a gate absent from
        # `results` is treated as a blocker (fail-closed — missing != passed).
        for gate in sorted(REQUIRED_GATES, key=lambda g: g.value):
            result = outcome_by_gate.get(gate)
            if result is None:
                blocking.append((gate, "gate not evaluated (missing result)"))
            elif not result.passed:
                blocking.append((gate, result.reason))
        if blocking:
            gates, reasons = zip(*blocking, strict=True)
            return UiDoneEvaluation(
                verdict=DoneVerdict.NOT_DONE,
                blocking_gates=gates,
                blocking_reasons=reasons,
            )
        # Reached only when every required gate is present and passed.
        return UiDoneEvaluation(
            verdict=DoneVerdict.DONE,
            blocking_gates=(),
            blocking_reasons=(),
        )
