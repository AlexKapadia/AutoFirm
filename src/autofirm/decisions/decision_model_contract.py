"""Typed contracts for the real-data decision-modeling engine (the `DecisionModel` seam).

What this does
--------------
Defines the abstraction every concrete decision model implements so that agents
can build, persist, and run models that turn a company's real operational/market
data into an EXPLAINABLE business recommendation (pricing, features, strategy):

* :class:`DecisionDriver` -- one named input and the magnitude/direction with
  which it pushed the recommendation, so the "why" is structured, not prose.
* :class:`DecisionRecommendation` -- the chosen action plus the ordered drivers
  that produced it. The drivers ARE the explanation; the chosen action is the
  "what". The contract guarantees the two cannot drift (CLAUDE.md §3.11).
* :class:`DecisionOutput` -- a model's full deterministic result: the computed
  metrics (exact, named) and the recommendation derived from them.
* :class:`DecisionModel` -- the abstract base: an immutable model with a stable
  ``model_id``, an owning ``role_id`` (the agent/role that owns it -- the memory
  access key), typed inputs, and a pure :meth:`compute` that is a deterministic
  function of those inputs alone.

Why it exists / where it sits
-----------------------------
This is the contract layer of ``autofirm.decisions`` -- the deterministic core
that the unit-economics, pricing, and operational-scenario models specialise.
Per the platform's real-data decision-modeling capability, the ENGINE is built
to run on a company's REAL data for live decisions; the PLATFORM'S OWN TESTS use
SYNTHETIC fixtures only (no real PII/client/confidential data -- CLAUDE.md
§3.12). The abstraction is therefore deliberately general (any company, any
model) and is argued correct from invariants, never fitted to one example
(§3.9).

Security / compliance invariants upheld
---------------------------------------
* **Fail closed (§5.6):** inputs are pydantic-validated at the boundary; an
  empty/blank ``model_id`` or ``role_id``, an empty driver label, or a
  recommendation whose drivers are empty is REFUSED at construction rather than
  silently accepted. Concrete models additionally refuse insufficient or
  contradictory data in :meth:`compute`.
* **Determinism (§3.11):** :meth:`compute` takes no clock, no randomness, no I/O
  -- identical inputs yield an identical :class:`DecisionOutput` every run, so a
  recommendation is reproducible and auditable.
* **Why-matches-what (§3.11):** :class:`DecisionRecommendation` binds the chosen
  action to the exact drivers that produced it; there is no path that emits an
  action without the structured reasons behind it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

__all__ = [
    "DecisionDriver",
    "DecisionInputs",
    "DecisionModel",
    "DecisionOutput",
    "DecisionRecommendation",
    "DriverDirection",
]

# A non-empty, length-bounded identifier/label. Bounding length is part of the
# fail-closed input defence (§5.6): an unbounded string is a resource-exhaustion
# and log-poisoning vector, exactly as in the memory record contract.
_Label = Annotated[str, StringConstraints(min_length=1, max_length=256, strip_whitespace=True)]


class DriverDirection(StrEnum):
    """Closed set: the direction in which an input pushed the recommendation.

    A closed enum (not free text) is what lets a reviewer reason about an
    explanation deterministically and lets tests assert direction exactly.
    """

    RAISES = "raises"  # this input pushed the recommended quantity UP
    LOWERS = "lowers"  # this input pushed the recommended quantity DOWN
    NEUTRAL = "neutral"  # this input was considered but did not move the result


class DecisionDriver(BaseModel):
    """One structured reason behind a recommendation: a labelled input + its effect.

    ``label`` names the input (e.g. ``"monthly_churn_rate"``); ``direction`` says
    whether it raised, lowered, or left unchanged the recommended quantity;
    ``contribution`` is the exact, signed magnitude of its effect in the model's
    own units. Keeping the effect EXACT (a :class:`~decimal.Decimal`, never a
    float) means the explanation carries zero numerical error (CLAUDE.md §3.11).
    """

    model_config = ConfigDict(frozen=True)

    label: _Label
    direction: DriverDirection
    contribution: Decimal  # signed, exact effect in the model's output units

    @field_validator("contribution")
    @classmethod
    def _contribution_is_finite(cls, value: Decimal) -> Decimal:
        # fail-closed: a NaN/Infinity contribution is a malformed explanation and
        # would silently corrupt any ranking/aggregation of drivers (§5.6).
        if not value.is_finite():
            raise ValueError("driver contribution must be a finite Decimal")
        return value


class DecisionRecommendation(BaseModel):
    """The chosen action plus the ordered drivers that produced it (why == what).

    ``action`` is the human/agent-actionable decision (e.g. a recommended price,
    "invest in feature X", "extend runway"). ``rationale`` is a one-line summary.
    ``drivers`` are the structured reasons, ordered most-influential first. The
    contract REQUIRES at least one driver so no action can ever be emitted without
    a reason behind it -- the binding that makes the "why" provably match the
    "what" (CLAUDE.md §3.11).
    """

    model_config = ConfigDict(frozen=True)

    action: _Label
    rationale: _Label
    drivers: tuple[DecisionDriver, ...]

    @field_validator("drivers")
    @classmethod
    def _at_least_one_driver(cls, value: tuple[DecisionDriver, ...]) -> tuple[DecisionDriver, ...]:
        # fail-closed: an unexplained recommendation is unacceptable (§3.11). A
        # recommendation with no driver is a defect, refused at the boundary.
        if not value:
            raise ValueError("a recommendation must carry at least one driver (why == what)")
        return value

    def primary_driver(self) -> DecisionDriver:
        """Return the single most-influential driver (the head of the ordered tuple).

        The model that builds the recommendation is responsible for ordering its
        drivers most-influential-first (the dominant, decision-making reason at the
        head). This contract is deliberately ORDER-PRESERVING: it stores the drivers
        exactly as supplied and never silently re-ranks them -- so the "primary"
        reported here is always the one the model DECLARED, even if a secondary
        driver happens to carry a larger signed ``contribution``. Re-sorting by raw
        magnitude here would let the explanation drift from the decision the model
        actually made (CLAUDE.md §3.11, why == what). Always defined: the contract
        guarantees a non-empty driver tuple.
        """
        return self.drivers[0]


class DecisionMetrics(BaseModel):
    """Named, exact metrics a model computes en route to its recommendation.

    A thin, frozen wrapper over an ordered mapping of metric name -> exact value,
    so callers (and the persistence seam) can serialise/inspect the deterministic
    intermediate quantities (e.g. LTV, payback months, recommended margin) without
    each model inventing its own ad-hoc shape.
    """

    model_config = ConfigDict(frozen=True)

    values: dict[_Label, Decimal]

    @field_validator("values")
    @classmethod
    def _values_finite(cls, value: dict[str, Decimal]) -> dict[str, Decimal]:
        # fail-closed: a non-finite metric is a silent-corruption vector (§5.6).
        for name, metric in value.items():
            if not metric.is_finite():
                raise ValueError(f"metric {name!r} must be a finite Decimal")
        return value

    def get(self, name: str) -> Decimal:
        """Return one metric by name, raising ``KeyError`` if absent (fail-closed)."""
        return self.values[name]


class DecisionOutput(BaseModel):
    """A model's full deterministic result: its metrics and the recommendation.

    Frozen so a produced result cannot be mutated after the fact, preserving the
    audit trail. ``metrics`` are the exact computed quantities; ``recommendation``
    is the action + drivers derived from them.
    """

    model_config = ConfigDict(frozen=True)

    metrics: DecisionMetrics
    recommendation: DecisionRecommendation


class DecisionInputs(BaseModel):
    """Base class for a concrete model's typed, validated input bundle.

    Concrete models subclass this with their own fields. Frozen so an input
    bundle, once validated at the boundary, cannot drift before/after
    :meth:`DecisionModel.compute` runs -- which is what keeps a recomputation
    deterministic over the SAME inputs (§3.11).
    """

    model_config = ConfigDict(frozen=True)


class DecisionModel[InputsT: DecisionInputs](ABC):
    """Abstract base: an owned, deterministic model from inputs to a recommendation.

    A model is identified by a stable ``model_id`` and owned by a ``role_id`` (the
    agent/role that built it -- this is the access key used by the persistence
    seam to file the model under its owner, mirroring the memory layer's
    owner-scoped writes). :meth:`compute` is the only behaviour: a PURE function of
    the supplied inputs (no clock, no randomness, no I/O), returning a
    :class:`DecisionOutput`. Concrete models keep each file focused and small
    (CLAUDE.md §5.7) and refuse insufficient/contradictory inputs fail-closed.
    """

    def __init__(self, *, model_id: str, role_id: str) -> None:
        """Bind the model's stable id and owning role, validating both fail-closed.

        Args:
            model_id: Stable identifier for this logical model (persistence key).
            role_id: The owning agent/role id -- the access key under which the
                model and its outputs are persisted.

        Raises:
            ValueError: If either id is blank after stripping (fail-closed, §5.6).
        """
        cleaned_model_id = model_id.strip()
        cleaned_role_id = role_id.strip()
        if not cleaned_model_id:  # fail-closed: a blank model id breaks persistence keys
            raise ValueError("model_id must be a non-empty identifier")
        if not cleaned_role_id:  # fail-closed: a blank owner cannot own/persist a model
            raise ValueError("role_id (owning agent/role) must be a non-empty identifier")
        self._model_id = cleaned_model_id
        self._role_id = cleaned_role_id

    @property
    def model_id(self) -> str:
        """The stable identifier of this logical model (its persistence key)."""
        return self._model_id

    @property
    def role_id(self) -> str:
        """The owning agent/role id -- the access key for persistence."""
        return self._role_id

    @property
    @abstractmethod
    def kind(self) -> str:
        """A short, stable label for the model family (e.g. ``"unit_economics"``).

        Used by the persistence seam to tag the stored model so an agent can
        recall "my pricing models" deterministically.
        """

    @abstractmethod
    def compute(self, inputs: InputsT) -> DecisionOutput:
        """Deterministically turn validated ``inputs`` into a :class:`DecisionOutput`.

        Pure: no clock, randomness, or I/O. Identical inputs MUST yield an
        identical output every run (§3.11). Must refuse insufficient or
        contradictory inputs with ``ValueError`` (fail-closed, §5.6) rather than
        emit a silently-wrong recommendation.
        """
