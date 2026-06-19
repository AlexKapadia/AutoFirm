"""Mutation-hardening tests pinning enum values, frozen/slots immutability, error messages.

These exist to KILL mutants the behavioural suites leave alive (CLAUDE.md §3.6): the exact
integer/string *value* of every enum member (a swapped value silently corrupts ordering or
the on-the-wire/serialised contract), the ``frozen=True`` and ``slots=True`` dataclass
guarantees (a flipped flag would let a "frozen" decision be mutated after scoring, or let a
typo'd attribute be silently swallowed), and the exact text of each fail-closed exception
(so a mutated diagnostic that no longer names the offending control is caught). Every
assertion targets a specific surviving mutant; none is tautological.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from autofirm.cockpit.core.approval_risk_model import (
    ApprovalDecision,
    PendingAction,
    ReversibilityClass,
    RiskLevel,
)
from autofirm.cockpit.core.autonomy_tier_model import (
    ActionKind,
    AutonomyTier,
    is_legal_transition,
    legal_next_tiers,
    tier_permits,
)
from autofirm.cockpit.core.budget_threshold_state import (
    BudgetBand,
    classify_budget_band,
)
from autofirm.cockpit.core.spend_rollup_model import (
    AgentSpend,
    RunSpendRollup,
    SpendEntry,
    StepSpend,
)
from autofirm.cockpit.core.spend_rollup_presenter import roll_up_run_spend
from autofirm.foundation.money.money_amount import Money

_USD = "USD"


def _usd(s: str) -> Money:
    return Money(Decimal(s), _USD)


# --- Exact enum VALUES (kills value-swap mutants) --------------------------------------


def test_autonomy_tier_values_are_pinned_exactly() -> None:
    assert AutonomyTier.READ_ONLY.value == 0
    assert AutonomyTier.SUPERVISED.value == 1
    assert AutonomyTier.FULL.value == 2


def test_action_kind_string_values_are_pinned_exactly() -> None:
    # The string value is the serialisation/audit contract; a mutated literal must fail.
    assert ActionKind.READ.value == "read"
    assert ActionKind.INTERNAL_WRITE.value == "internal_write"
    assert ActionKind.EXTERNAL_SIDE_EFFECT.value == "external_side_effect"
    assert ActionKind.IRREVERSIBLE.value == "irreversible"
    assert ActionKind.SPEND_COMMIT.value == "spend_commit"
    assert ActionKind.KILL_SWITCH.value == "kill_switch"


def test_risk_level_values_are_pinned_and_strictly_ordered() -> None:
    assert RiskLevel.LOW.value == 0
    assert RiskLevel.MEDIUM.value == 1
    assert RiskLevel.HIGH.value == 2
    assert RiskLevel.CRITICAL.value == 3
    assert RiskLevel.LOW < RiskLevel.MEDIUM < RiskLevel.HIGH < RiskLevel.CRITICAL


def test_reversibility_string_values_are_pinned_exactly() -> None:
    assert ReversibilityClass.REVERSIBLE.value == "reversible"
    assert ReversibilityClass.PARTIALLY_REVERSIBLE.value == "partially_reversible"
    assert ReversibilityClass.IRREVERSIBLE.value == "irreversible"


def test_approval_decision_string_values_are_pinned_exactly() -> None:
    assert ApprovalDecision.AUTO_APPROVE.value == "auto_approve"
    assert ApprovalDecision.REQUIRE_HUMAN.value == "require_human"
    assert ApprovalDecision.REFUSE.value == "refuse"


def test_budget_band_values_are_pinned_and_strictly_ordered() -> None:
    assert BudgetBand.OK.value == 0
    assert BudgetBand.WARN_50.value == 1
    assert BudgetBand.WARN_80.value == 2
    assert BudgetBand.CRIT_95.value == 3
    assert BudgetBand.OK < BudgetBand.WARN_50 < BudgetBand.WARN_80 < BudgetBand.CRIT_95


# --- frozen=True: instances cannot be mutated after construction -----------------------


def _sample_pending() -> PendingAction:
    return PendingAction(
        action_kind=ActionKind.READ,
        risk_level=RiskLevel.LOW,
        reversibility=ReversibilityClass.REVERSIBLE,
        requires_external_call=False,
        estimated_blast_radius=0,
    )


@pytest.mark.parametrize(
    ("instance", "attr", "value"),
    [
        (_sample_pending(), "risk_level", RiskLevel.CRITICAL),
        (SpendEntry("a", "s1", _usd("1.00")), "amount", _usd("9.99")),
        (StepSpend("s1", _usd("1.00")), "amount", _usd("9.99")),
        (AgentSpend("a", _usd("1.00"), BudgetBand.OK, ()), "total", _usd("9.99")),
        (RunSpendRollup(_usd("1.00"), BudgetBand.OK, ()), "total", _usd("9.99")),
    ],
)
def test_value_types_are_frozen(instance: object, attr: str, value: object) -> None:
    # frozen=True: a decision/record must NOT be mutable after it is built — a flipped
    # frozen flag (mutant) would allow tampering between scoring and audit.
    with pytest.raises((AttributeError, TypeError)):
        setattr(instance, attr, value)


@pytest.mark.parametrize(
    "instance",
    [
        _sample_pending(),
        SpendEntry("a", "s1", _usd("1.00")),
        StepSpend("s1", _usd("1.00")),
        AgentSpend("a", _usd("1.00"), BudgetBand.OK, ()),
        RunSpendRollup(_usd("1.00"), BudgetBand.OK, ()),
    ],
)
def test_value_types_use_slots_no_dict_no_stray_attributes(instance: object) -> None:
    # slots=True: the type has NO __dict__, so a typo'd/forged attribute is rejected rather
    # than silently absorbed. A flipped slots flag (mutant) would grow a __dict__ here.
    assert not hasattr(instance, "__dict__")
    with pytest.raises((AttributeError, TypeError)):
        instance.smuggled_attribute = "x"  # type: ignore[attr-defined]


# --- Exception MESSAGES name the control (kills message-string mutants) ----------------


def test_pending_action_messages_name_the_offending_field() -> None:
    with pytest.raises(TypeError, match="action_kind must be an ActionKind"):
        PendingAction("read", RiskLevel.LOW, ReversibilityClass.REVERSIBLE, False, 0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="risk_level must be a RiskLevel"):
        PendingAction(ActionKind.READ, 0, ReversibilityClass.REVERSIBLE, False, 0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="reversibility must be a ReversibilityClass"):
        PendingAction(ActionKind.READ, RiskLevel.LOW, "reversible", False, 0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="requires_external_call must be a bool"):
        PendingAction(ActionKind.READ, RiskLevel.LOW, ReversibilityClass.REVERSIBLE, 1, 0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="estimated_blast_radius must be >= 0"):
        PendingAction(ActionKind.READ, RiskLevel.LOW, ReversibilityClass.REVERSIBLE, False, -1)
    with pytest.raises(TypeError, match="estimated_blast_radius must be an int"):
        PendingAction(ActionKind.READ, RiskLevel.LOW, ReversibilityClass.REVERSIBLE, False, 1.5)  # type: ignore[arg-type]


def test_scorer_messages_name_the_offending_argument() -> None:
    from autofirm.cockpit.core.approval_risk_scorer import decide_approval

    with pytest.raises(TypeError, match="action must be a PendingAction"):
        decide_approval("x", AutonomyTier.FULL)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="tier must be an AutonomyTier"):
        decide_approval(_sample_pending(), "FULL")  # type: ignore[arg-type]


def test_autonomy_messages_name_the_offending_argument() -> None:
    with pytest.raises(TypeError, match="tier must be an AutonomyTier"):
        tier_permits("FULL", ActionKind.READ)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="action must be an ActionKind"):
        tier_permits(AutonomyTier.FULL, "READ")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="frm must be an AutonomyTier"):
        is_legal_transition("READ_ONLY", AutonomyTier.FULL)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="to must be an AutonomyTier"):
        is_legal_transition(AutonomyTier.FULL, "READ_ONLY")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="frm must be an AutonomyTier"):
        legal_next_tiers("READ_ONLY")  # type: ignore[arg-type]


def test_budget_messages_name_the_offending_control() -> None:
    with pytest.raises(TypeError, match="spent must be Money"):
        classify_budget_band("1.00", _usd("100.00"))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="budget must be Money"):
        classify_budget_band(_usd("1.00"), "100.00")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cannot compare USD spend against GBP budget"):
        classify_budget_band(_usd("1.00"), Money(Decimal("100.00"), "GBP"))
    with pytest.raises(ValueError, match="budget must be strictly positive"):
        classify_budget_band(_usd("1.00"), _usd("0.00"))
    with pytest.raises(ValueError, match="spent must be non-negative"):
        classify_budget_band(_usd("-1.00"), _usd("100.00"))


def test_spend_entry_messages_name_the_offending_field() -> None:
    with pytest.raises(TypeError, match="agent_id must be a str"):
        SpendEntry(5, "s1", _usd("1.00"))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="step_id must be a str"):
        SpendEntry("a", 5, _usd("1.00"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="agent_id must be a non-empty identifier"):
        SpendEntry("  ", "s1", _usd("1.00"))
    with pytest.raises(ValueError, match="step_id must be a non-empty identifier"):
        SpendEntry("a", "", _usd("1.00"))
    with pytest.raises(TypeError, match="amount must be a Money"):
        SpendEntry("a", "s1", Decimal("1.00"))  # type: ignore[arg-type]


def test_presenter_messages_name_the_offending_control() -> None:
    with pytest.raises(TypeError, match="budget must be Money"):
        roll_up_run_spend([], budget="100.00", currency=_USD)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="budget currency GBP does not match run currency USD"):
        roll_up_run_spend([], budget=Money(Decimal("1.00"), "GBP"), currency=_USD)
    with pytest.raises(TypeError, match="every ledger member must be a SpendEntry"):
        roll_up_run_spend([1], budget=_usd("100.00"), currency=_USD)  # type: ignore[list-item]
    with pytest.raises(ValueError, match="entry currency GBP does not match run currency USD"):
        roll_up_run_spend(
            [SpendEntry("a", "s1", Money(Decimal("1.00"), "GBP"))],
            budget=_usd("100.00"),
            currency=_USD,
        )
