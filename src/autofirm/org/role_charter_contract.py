"""The typed role charter (AgentSpec) every manager authors for a direct report.

What this does
--------------
Defines :class:`RoleCharter` — the immutable, validated specification of a single
role in the org: its responsibilities, ownership scope, the manager that owns and
*authored* it, and the JCM completeness fields the A1.5 synthesis mandates. A
charter is the contract a role is spawned against; no role can exist without a
manager-authored charter (the no-spawn-without-spec invariant lives here as
construction-time validation, and is re-checked by the lifecycle engine).

Why it exists / where it sits
-----------------------------
Per ``docs/research/A1.5-auto-hiring-role-creation/SYNTHESIS.md`` §2(2), a role
charter fuses the **Job Characteristics Model** five dimensions [03] with
**role-set / single-accountable** rights [04][09]: ``responsibilities``
(variety/significance), ``owned_artifacts`` (task identity == single-writer),
``ownership_scope`` (autonomy), and ``success_signal`` (feedback). The synthesis
gives a hard **MPS-collapse completeness gate**: a charter missing autonomy
(``ownership_scope``) or feedback (``success_signal``) is rejected, because a
role with no autonomy or no feedback collapses the Motivating-Potential-Score to
zero and is mis-specified by construction (§2(2), [03]).

Security / compliance invariants upheld
---------------------------------------
* **No-spawn-without-spec (fail-closed, CLAUDE.md §5.6):** a charter is the only
  way to describe a role; an empty/incomplete charter is refused at construction
  so a role can never be spawned from an under-specified spec.
* **Single-accountable (single-writer seed, [09]):** ``owned_artifacts`` declares
  exactly which artifacts this role is the sole owner of; the ownership ledger
  enforces non-overlap, but the charter is where ownership is *authored*.
* **Manager-authored (audited authorship, A6):** ``authored_by`` records which
  manager wrote the spec — every role's spec traces to its owning manager, never
  to itself (no self-authoring; enforced by the lifecycle engine).
* **Immutable:** frozen once built; a re-scope produces a NEW charter rather than
  mutating an existing one (append-only authorship trail).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.org.org_identifiers import ArtifactId, RoleId

__all__ = ["RoleCharter", "ROOT_AUTHOR"]

# The sentinel author of the root role: the founding act has no managing role
# above it, so the root charter is authored by this constant rather than by a
# (non-existent) parent. Every NON-root charter must be authored by a real,
# existing manager role (enforced fail-closed in the lifecycle engine).
ROOT_AUTHOR: RoleId = RoleId("__founder__")


class RoleCharter(BaseModel):
    """An immutable, manager-authored specification of one org role.

    Construction is fail-closed: the JCM completeness gate (CLAUDE.md-cited A1.5
    §2(2)) refuses a charter that lacks autonomy (``ownership_scope``) or feedback
    (``success_signal``), and refuses empty responsibilities — an under-specified
    role can never be spawned.
    """

    model_config = ConfigDict(frozen=True)

    role_id: RoleId  # this role's stable identity (roles-as-data, [04])
    title: str  # human-readable role title (e.g. "FP&A Lead")
    responsibilities: tuple[str, ...]  # JCM variety+significance: what it must do
    ownership_scope: str  # JCM autonomy: the decision boundary it owns
    success_signal: str  # JCM feedback: how its output is judged
    owned_artifacts: frozenset[ArtifactId]  # the artifacts it is sole owner of
    manager_id: RoleId | None  # the managing role this reports to (None == root)
    authored_by: RoleId  # the manager role that WROTE this spec (audited authorship)

    @field_validator("title", "ownership_scope", "success_signal")
    @classmethod
    def _required_text_non_empty(cls, value: str) -> str:
        # fail-closed: MPS-collapse gate ([03]) — a role with no autonomy
        # (ownership_scope) or no feedback (success_signal), or no title, is
        # mis-specified by construction and must be refused, not spawned.
        if not value.strip():
            raise ValueError("charter text fields must be non-empty (MPS-collapse gate)")
        return value

    @field_validator("responsibilities")
    @classmethod
    def _at_least_one_responsibility(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        # fail-closed: a role that does nothing is not a role. JCM variety/identity
        # requires at least one concrete responsibility.
        if not value:
            raise ValueError("a role must declare at least one responsibility")
        if any(not r.strip() for r in value):
            raise ValueError("responsibilities must be non-empty strings")
        return value

    def is_root(self) -> bool:
        """Return True if this is the root role (no managing role above it)."""
        return self.manager_id is None
