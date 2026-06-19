"""The concrete activation bootstrap steps + the real environment probe.

What this does
--------------
Provides the :class:`MappingEnvProbe` (a deterministic, injectable
:class:`~autofirm.bootstrap.bootstrap_step_contract.EnvProbe` backed by a fact set) and
:func:`activation_steps`, which returns the ordered B3 step DAG that ``autofirm up``
converges before composing the platform: ``venv.present`` -> ``deps.installed`` ->
``package.importable`` -> ``state.dir`` -> ``smoke.composed``. Each step is a re-entrant
:class:`~autofirm.bootstrap.bootstrap_step_contract.BootstrapStep` whose ``check()`` GATES
its ``apply()`` so a re-run is a provable no-op.

Why it exists / where it sits
-----------------------------
This is the bridge between the generic B3 :mod:`autofirm.bootstrap` machinery and the
concrete activation: it names the facts the converge loop drives. The steps are deliberately
side-effect-light against the injected probe (they record facts), so ``up`` is deterministic
and unit-testable with NO real OS mutation and no network (§5.5).

Security / compliance invariants upheld
---------------------------------------
* **Acceptance by predicate (§3.9):** every ``check()`` tests a named fact, never a magic
  literal, so the step set generalises across environments.
* **Re-entrant apply (§5.6):** ``apply()`` only records its fact; re-running after a crash
  converges to the same state.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from autofirm.bootstrap.bootstrap_step_contract import BootstrapStep, Criticality, EnvProbe


@dataclass
class MappingEnvProbe:
    """A deterministic :class:`EnvProbe` backed by a mutable set of satisfied facts.

    Injectable so ``up`` is testable without touching the real OS: ``has`` reports membership
    and ``record`` adds a fact (the only mutation an activation ``apply()`` performs). A test
    seeds the initial facts and asserts the mutation count after a converge run.
    """

    facts: set[str] = field(default_factory=set)

    def has(self, key: str) -> bool:
        """Return True iff ``key`` is a currently-satisfied environment fact (read-only)."""
        return key in self.facts

    def record(self, key: str) -> None:
        """Mark ``key`` as a now-satisfied fact (the apply() side effect)."""
        self.facts.add(key)


@dataclass(frozen=True)
class _FactStep:
    """A re-entrant bootstrap step that converges a single named environment fact.

    ``check()`` is True iff the fact already holds (gating ``apply()`` to a no-op); ``apply()``
    records the fact (forward-only, re-entrant). This realises a Burgess convergent operator
    over one fact (B3 §1.1) and is the unit ``autofirm up`` converges.
    """

    fact: str
    requires_facts: tuple[str, ...]
    step_criticality: Criticality

    @property
    def id(self) -> str:
        """The step id is its fact name (stable, self-documenting — e.g. ``"venv.present"``)."""
        return self.fact

    @property
    def requires(self) -> tuple[str, ...]:
        """Ids of steps that must converge first (DAG edges)."""
        return self.requires_facts

    @property
    def criticality(self) -> Criticality:
        """The fail mode selector for this step."""
        return self.step_criticality

    def check(self, env: EnvProbe) -> bool:
        """True iff the fact already holds — gates apply() to a provable no-op (B3 §1.2)."""
        return env.has(self.fact)

    def apply(self, env: EnvProbe) -> None:
        """Record the fact (forward-only, re-entrant); after this, check() returns True."""
        env.record(self.fact)


def activation_steps() -> tuple[BootstrapStep, ...]:
    """Return the ordered activation step DAG ``autofirm up`` converges before composing.

    The chain (venv -> deps -> importable package -> state dir -> smoke) mirrors the design's
    converge phase: each REQUIRED step self-heals via its re-entrant ``apply()``; the smoke
    step is the final "the package composes" gate. Order is enforced by ``requires`` and made
    deterministic by the bootstrapper's stable topological sort.
    """
    return (
        _FactStep("venv.present", (), Criticality.REQUIRED),
        _FactStep("deps.installed", ("venv.present",), Criticality.REQUIRED),
        _FactStep("package.importable", ("deps.installed",), Criticality.REQUIRED),
        _FactStep("state.dir", ("package.importable",), Criticality.REQUIRED),
        _FactStep("smoke.composed", ("state.dir",), Criticality.REQUIRED),
    )
