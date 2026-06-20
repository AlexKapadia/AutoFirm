"""The idempotent, crash-safe environment bootstrapper: the converge loop over steps.

What this does
--------------
Defines :class:`IdempotentEnvironmentBootstrapper`, which runs a set of
:class:`~autofirm.bootstrap.bootstrap_step_contract.BootstrapStep` s through a MAPE-K
converge loop (B3 source 03/04): topologically order by ``requires``, then for each step
``if not step.check(env): step.apply(env)``. The result is a deterministic, named terminal
state — every step resolved to SATISFIED/APPLIED/DEGRADED/FAILED — never an unhandled
exception. A completed run is recorded to a crash-atomic ledger (write-temp -> fsync ->
``os.replace`` -> fsync-dir, B3 source 05) so a resume can skip fast; but ``check()`` stays
authoritative (the ledger is an audit/optimisation cache, not the source of truth — B3 §1.2
clause 6).

Why it exists / where it sits
-----------------------------
This is the converge half of ``autofirm up`` (the compose/supervise/self-test half lives in
:mod:`autofirm.runtime`). ``autofirm doctor`` reuses the same steps read-only via
:mod:`autofirm.bootstrap.bootstrap_doctor_report`.

Security / compliance invariants upheld
---------------------------------------
* **check() gates apply() (B3 §1.2 clause 2):** asserted in the loop — ``apply()`` is only
  reached when ``check()`` returned False. Re-running on a converged tree mutates nothing.
* **Crash-atomic ledger (B3 §1.2 clause 5):** the durable state is written via atomic
  rename, so a crash leaves it fully-old or fully-new, never torn.
* **Deterministic order (B3 §1.2 clause 7):** the topological sort is stable across runs.
* **Fail-closed terminal state (§5.6):** a SECURITY/REQUIRED step whose ``check()`` is still
  False after ``apply()`` resolves to FAILED (reported), never silently skipped.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from autofirm.bootstrap.bootstrap_step_contract import (
    BootstrapStep,
    Criticality,
    EnvProbe,
    StepOutcome,
    StepState,
)


@dataclass(frozen=True)
class BootstrapResult:
    """The terminal result of one converge run: every step's outcome + the mutation count.

    ``mutations`` is the number of steps whose ``apply()`` actually ran this pass — it is 0
    on a converged tree, which is the asserted no-op signal for idempotency (B3 §3 item 2).
    """

    outcomes: tuple[StepOutcome, ...]
    mutations: int

    @property
    def converged(self) -> bool:
        """True iff no step ended FAILED (SATISFIED/APPLIED/DEGRADED are all acceptable)."""
        # DEGRADED is acceptable (platform stays UP); only a FAILED security/required step
        # makes the run non-converged (fail-closed reporting).
        return all(o.state is not StepState.FAILED for o in self.outcomes)


def _topological_order(steps: tuple[BootstrapStep, ...]) -> tuple[BootstrapStep, ...]:
    """Return the steps in a stable topological order honouring ``requires`` (B3 clause 7).

    Deterministic tie-break: among ready steps, the lowest ``id`` is emitted first, so the
    same step set always yields the same order across runs and OSes (no wall-clock, no set
    iteration nondeterminism). Raises ``ValueError`` on an unknown requirement or a cycle —
    fail-closed: an unsatisfiable DAG is a defect, not something to silently reorder.
    """
    by_id = {s.id: s for s in steps}
    for step in steps:
        for req in step.requires:
            if req not in by_id:
                # fail-closed: a dangling requirement means the DAG is mis-specified.
                raise ValueError(f"step {step.id!r} requires unknown step {req!r}")
    ordered: list[BootstrapStep] = []
    done: set[str] = set()
    remaining = dict(by_id)
    # Bounded-iteration guard (CLAUDE.md §7.2): each pass emits at least one ready step, so a
    # well-formed DAG of N steps always drains in <= N passes. Capping the passes at exactly
    # ``len(steps)`` via a bounded ``range`` (rather than an open ``while remaining``) makes it
    # structurally impossible for a mutated loop body to busy-spin forever — mutmut 2.x cannot
    # abort a busy Python loop on Windows. The cap is a real invariant, not a test-only hack:
    # a valid acyclic graph never needs an (N+1)th pass.
    for _ in range(len(steps)):
        if not remaining:
            # Drained early (independent steps resolve in one pass): return the order so far.
            # A direct ``return`` (rather than ``break``) avoids an equivalent ``break``->
            # ``continue`` mutant — the early exit is then provable by the mutation gate (§3.6).
            return tuple(ordered)
        ready = sorted(
            (s for s in remaining.values() if all(r in done for r in s.requires)),
            key=lambda s: s.id,
        )
        if not ready:
            # fail-closed: steps remain but none is ready => a dependency cycle. Bounding the
            # loop ALSO catches this on the first stuck pass, so the raise is reachable & tested.
            raise ValueError(f"dependency cycle among steps: {sorted(remaining)}")
        for step in ready:
            ordered.append(step)
            done.add(step.id)
            del remaining[step.id]
    return tuple(ordered)


class IdempotentEnvironmentBootstrapper:
    """Runs steps through the idempotent converge loop with a crash-atomic ledger.

    Args:
        steps: The bootstrap steps to converge (ordered internally by ``requires``).
        ledger_path: Where the durable completed-step ledger is written (atomic rename).
            ``None`` disables ledger persistence (e.g. a pure in-memory test).
    """

    def __init__(
        self,
        steps: tuple[BootstrapStep, ...],
        *,
        ledger_path: Path | None = None,
    ) -> None:
        """Bind the steps and ledger path; topo-sort eagerly so a bad DAG fails fast."""
        self._ledger_path = ledger_path
        self._ordered = _topological_order(steps)

    def converge(self, env: EnvProbe) -> BootstrapResult:
        """Run check()->apply() over every step in order; return the named terminal result.

        For each step: ``check()`` is consulted first and GATES ``apply()`` — ``apply()`` is
        only invoked on a False check (the provable-no-op contract). After a converging
        ``apply()``, ``check()`` is re-verified; if a SECURITY/REQUIRED step is still
        unconverged it resolves FAILED (fail-closed), an OPTIONAL one resolves DEGRADED.
        """
        outcomes: list[StepOutcome] = []
        mutations = 0
        for step in self._ordered:
            if step.check(env):
                # check() gated apply() to a no-op: the step is already converged.
                outcomes.append(_outcome(step, StepState.SATISFIED, "already_converged"))
                continue
            step.apply(env)  # forward-only, re-entrant; only reached on a False check()
            mutations += 1
            if step.check(env):
                outcomes.append(_outcome(step, StepState.APPLIED, "converged_this_run"))
            else:
                outcomes.append(_step_unconverged_outcome(step))
        result = BootstrapResult(outcomes=tuple(outcomes), mutations=mutations)
        self._persist(result)
        return result

    def _persist(self, result: BootstrapResult) -> None:
        """Write the completed-step ledger via the crash-atomic rename protocol (B3 §1.2.5).

        write temp -> fsync(temp) -> os.replace(temp, target) -> fsync(dir): a crash leaves
        the ledger fully-old or fully-new, never partially written. The ledger is an audit /
        skip-fast cache; ``check()`` remains the source of truth on the next run.
        """
        if self._ledger_path is None:
            return
        payload = json.dumps(
            {o.step_id: o.state.value for o in result.outcomes},
            sort_keys=True,  # deterministic bytes: same state set -> identical ledger file
        ).encode("utf-8")
        tmp = self._ledger_path.with_suffix(self._ledger_path.suffix + ".tmp")
        with tmp.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())  # data durable BEFORE the swap (ordering enforced)
        os.replace(tmp, self._ledger_path)  # atomic dir-entry swap: old-or-new, never torn
        _fsync_directory(self._ledger_path.parent)


def _fsync_directory(directory: Path) -> None:
    """Best-effort fsync of a directory so a preceding rename is itself durable (B3 §1.2.5).

    POSIX makes a directory fsync durable; Windows refuses to open/fsync a directory handle
    (PermissionError). The preceding ``os.replace`` is already atomic on both, so a platform
    that cannot fsync the dir still has a torn-free ledger — we degrade to best-effort
    durability of the rename rather than fail the bootstrap.
    """
    try:
        dir_fd = os.open(str(directory), os.O_RDONLY)
    except OSError:  # Windows: cannot open a directory handle — the rename is still atomic
        return
    try:
        os.fsync(dir_fd)  # make the rename itself durable (POSIX)
    except OSError:  # pragma: no cover - some filesystems refuse dir fsync; rename still atomic
        pass
    finally:
        os.close(dir_fd)


def _outcome(step: BootstrapStep, state: StepState, detail: str) -> StepOutcome:
    """Build a :class:`StepOutcome` capturing a step's id, criticality, and final state."""
    return StepOutcome(
        step_id=step.id,
        criticality=step.criticality,
        state=state,
        detail=detail,
    )


def _step_unconverged_outcome(step: BootstrapStep) -> StepOutcome:
    """Resolve a step that is STILL unconverged after apply(): DEGRADED vs FAILED.

    OPTIONAL -> DEGRADED (bulkhead; platform stays UP). SECURITY/REQUIRED -> FAILED
    (fail-closed; reported, never silently skipped — §5.6).
    """
    if step.criticality is Criticality.OPTIONAL:
        return _outcome(step, StepState.DEGRADED, "optional_step_unconverged_capability_degraded")
    return _outcome(step, StepState.FAILED, "critical_step_unconverged_failed_closed")
