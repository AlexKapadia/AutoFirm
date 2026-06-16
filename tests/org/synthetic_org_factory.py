"""Synthetic, deterministic builders for the dynamic-org test suite.

What this provides
------------------
Side-effect-free factories for valid :class:`RoleCharter` instances, a freshly
founded :class:`DynamicOrg`, and a pinned :class:`FrozenClock` /
:class:`SequentialIdGenerator`, so every test starts from a known, reproducible
org. No network, no real I/O, no real PII — synthetic only (CLAUDE.md §5.5/§3.12).

These builders deliberately produce *valid* charters by default; tests construct
the invalid/adversarial variants inline so the failure each test targets is
explicit and local.
"""

from __future__ import annotations

from datetime import UTC, datetime

from autofirm.org.org_identifiers import (
    ArtifactId,
    FrozenClock,
    RoleId,
    SequentialIdGenerator,
)
from autofirm.org.org_lifecycle_engine import DynamicOrg
from autofirm.org.role_charter_contract import ROOT_AUTHOR, RoleCharter

# A fixed epoch so audit timestamps are deterministic and assertable.
EPOCH = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)


def charter(
    role_id: str,
    manager_id: str | None,
    authored_by: str,
    artifacts: frozenset[str] = frozenset(),
) -> RoleCharter:
    """Build a valid charter; ids are wrapped into their NewType aliases."""
    return RoleCharter(
        role_id=RoleId(role_id),
        title=role_id.upper(),
        responsibilities=(f"{role_id}-does-its-job",),
        ownership_scope=f"{role_id}-scope",
        success_signal=f"{role_id}-kpi",
        owned_artifacts=frozenset(ArtifactId(a) for a in artifacts),
        manager_id=RoleId(manager_id) if manager_id is not None else None,
        authored_by=RoleId(authored_by),
    )


def root_charter(role_id: str = "ceo", artifacts: frozenset[str] = frozenset()) -> RoleCharter:
    """Build a valid root charter authored by the founder sentinel."""
    return RoleCharter(
        role_id=RoleId(role_id),
        title=role_id.upper(),
        responsibilities=("run-the-company",),
        ownership_scope="company",
        success_signal="enterprise-value",
        owned_artifacts=frozenset(ArtifactId(a) for a in artifacts),
        manager_id=None,
        authored_by=ROOT_AUTHOR,
    )


def fresh_clock(step_seconds: float = 1.0) -> FrozenClock:
    """A deterministic clock starting at EPOCH, advancing ``step_seconds`` per call."""
    return FrozenClock(EPOCH, step_seconds=step_seconds)


def founded_org(root_id: str = "ceo", artifacts: frozenset[str] = frozenset()) -> DynamicOrg:
    """A freshly founded org with a single root role and pinned determinism seams."""
    return DynamicOrg.found(
        root_charter(root_id, artifacts), fresh_clock(), SequentialIdGenerator()
    )
