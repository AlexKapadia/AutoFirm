"""Exact ``.value`` and ordering assertions for every core enum member (CLAUDE.md §3.6).

These kill two mutant families on the enum members:
* **int-bump** on an ``IntEnum`` value (``1`` -> ``2``) -- caught by pinning the exact
  ``.value`` AND the ordering chain (a bumped value collides with its neighbour and breaks
  strict ``<`` ordering / contiguity).
* **string-wrap** on a ``str``-valued ``Enum`` (``"x"`` -> ``"XXxXX"``) -- caught by the
  exact ``== "x"`` on each member's ``.value`` (the on-the-wire / audit-serialisation
  contract).
"""

from __future__ import annotations

from autofirm.cockpit.core.approval_risk_model import (
    ApprovalDecision,
    ReversibilityClass,
    RiskLevel,
)
from autofirm.cockpit.core.autonomy_tier_model import ActionKind, AutonomyTier
from autofirm.cockpit.core.budget_threshold_state import BudgetBand


def test_risk_level_values_and_ordering_are_exact() -> None:
    assert RiskLevel.LOW.value == 0
    assert RiskLevel.MEDIUM.value == 1
    assert RiskLevel.HIGH.value == 2
    assert RiskLevel.CRITICAL.value == 3
    # ordered, distinct and contiguous -> an int-bump breaks this chain.
    assert RiskLevel.LOW < RiskLevel.MEDIUM < RiskLevel.HIGH < RiskLevel.CRITICAL
    assert [m.value for m in RiskLevel] == [0, 1, 2, 3]


def test_reversibility_string_values_are_exact() -> None:
    assert ReversibilityClass.REVERSIBLE.value == "reversible"
    assert ReversibilityClass.PARTIALLY_REVERSIBLE.value == "partially_reversible"
    assert ReversibilityClass.IRREVERSIBLE.value == "irreversible"


def test_approval_decision_string_values_are_exact() -> None:
    assert ApprovalDecision.AUTO_APPROVE.value == "auto_approve"
    assert ApprovalDecision.REQUIRE_HUMAN.value == "require_human"
    assert ApprovalDecision.REFUSE.value == "refuse"


def test_autonomy_tier_values_and_ordering_are_exact() -> None:
    assert AutonomyTier.READ_ONLY.value == 0
    assert AutonomyTier.SUPERVISED.value == 1
    assert AutonomyTier.FULL.value == 2
    assert AutonomyTier.READ_ONLY < AutonomyTier.SUPERVISED < AutonomyTier.FULL
    assert [m.value for m in AutonomyTier] == [0, 1, 2]


def test_action_kind_string_values_are_exact() -> None:
    assert ActionKind.READ.value == "read"
    assert ActionKind.INTERNAL_WRITE.value == "internal_write"
    assert ActionKind.EXTERNAL_SIDE_EFFECT.value == "external_side_effect"
    assert ActionKind.IRREVERSIBLE.value == "irreversible"
    assert ActionKind.SPEND_COMMIT.value == "spend_commit"
    assert ActionKind.KILL_SWITCH.value == "kill_switch"


def test_budget_band_values_and_ordering_are_exact() -> None:
    assert BudgetBand.OK.value == 0
    assert BudgetBand.WARN_50.value == 1
    assert BudgetBand.WARN_80.value == 2
    assert BudgetBand.CRIT_95.value == 3
    assert BudgetBand.OK < BudgetBand.WARN_50 < BudgetBand.WARN_80 < BudgetBand.CRIT_95
    assert [m.value for m in BudgetBand] == [0, 1, 2, 3]
