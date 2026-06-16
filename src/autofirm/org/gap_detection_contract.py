"""The org-gap signal that triggers automatic role-creation (gap-detect stage).

What this does
--------------
Defines :class:`OrgGap`, the typed signal a managing role emits when it detects a
capability/coverage gap in its sub-org, and :class:`GapKind`, the four
established gap kinds from the A1.5 synthesis. A gap is the *input* to automatic
role-creation: the lifecycle engine takes a gap plus the managing role's authored
charter for the new role and runs the gap-detect -> role-spec -> spawn pipeline.

Why it exists / where it sits
-----------------------------
Per ``docs/research/A1.5-auto-hiring-role-creation/SYNTHESIS.md`` §2(1), gap-detect
runs continuously and emits four complementary gap kinds: SHORTAGE (headcount),
SKILL_GAP (competency), ROLE_COVERAGE_GAP (a missing function archetype), and
COORDINATION_LOAD (information-processing load over capacity). This module is the
typed contract for that signal; it deliberately models the *signal*, not the
detection heuristics (which depend on live telemetry) — so the engine stays
deterministic and the gap source can be swapped without touching the lifecycle.

Security / compliance invariants upheld
---------------------------------------
* **Decision-gated authorship (fail-closed, [09] / CLAUDE.md §5.6):** a gap names
  the ``detected_by`` managing role; the lifecycle engine refuses to auto-create a
  role unless that role exists and is the authoring manager — no agent
  unilaterally spawns roles outside the hierarchy.
* **Validated input (§5.6):** a gap with an empty rationale or non-positive
  severity is refused at construction, so a malformed signal cannot drive a spawn.
* **Immutable:** the gap is frozen; it is an auditable record of *why* a role was
  created.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator

from autofirm.org.org_identifiers import RoleId

__all__ = ["GapKind", "OrgGap"]


class GapKind(StrEnum):
    """The four complementary org-gap kinds (A1.5 §2(1); deterministic menu)."""

    SHORTAGE = "SHORTAGE"  # required - available headcount over a window [01]
    SKILL_GAP = "SKILL_GAP"  # target - current competency proficiency [02]
    ROLE_COVERAGE_GAP = "ROLE_COVERAGE_GAP"  # a needed function archetype uncovered [12]
    COORDINATION_LOAD = "COORDINATION_LOAD"  # info-processing load exceeds capacity [13]


class OrgGap(BaseModel):
    """An immutable, audited signal that a managing role detected a coverage gap.

    The gap is the input to automatic role-creation; it carries which manager
    detected it (so authorship is decision-gated) and a deterministic rationale
    (which feeds the audit trail's ``detail`` — the 'why' a role was created).
    """

    model_config = ConfigDict(frozen=True)

    kind: GapKind
    detected_by: RoleId  # the managing role that will author the filling role
    rationale: str  # deterministic, PII-free 'why' (audited)
    severity: int  # positive magnitude; higher = more urgent (deterministic ranking)

    @field_validator("rationale")
    @classmethod
    def _rationale_non_empty(cls, value: str) -> str:
        # fail-closed: a gap with no stated reason cannot justify creating a role.
        if not value.strip():
            raise ValueError("gap rationale must be non-empty (audit 'why')")
        return value

    @field_validator("severity")
    @classmethod
    def _severity_positive(cls, value: int) -> int:
        # fail-closed: a non-positive-severity 'gap' is not actually a gap.
        if value <= 0:
            raise ValueError("gap severity must be > 0")
        return value
