"""Exact-equality assertions on the two fail-closed messages in the approval scorer.

Why this file exists (CLAUDE.md §3.6)
-------------------------------------
``decide_approval`` rejects malformed inputs with f-string diagnostics. The sibling
``test_approval_risk_scorer__fail_closed_decision.py`` is already 316 lines, so these
message-pinning tests live here. ``pytest.raises(match=...)`` is a regex SUBSTRING search
that the string-wrap mutant survives; passing a known wrong type (``int``) and asserting
the resolved string with ``==`` kills it.
"""

from __future__ import annotations

import pytest

from autofirm.cockpit.core.approval_risk_model import (
    PendingAction,
    ReversibilityClass,
    RiskLevel,
)
from autofirm.cockpit.core.approval_risk_scorer import decide_approval
from autofirm.cockpit.core.autonomy_tier_model import ActionKind, AutonomyTier


def _benign_action() -> PendingAction:
    return PendingAction(
        action_kind=ActionKind.READ,
        risk_level=RiskLevel.LOW,
        reversibility=ReversibilityClass.REVERSIBLE,
        requires_external_call=False,
        estimated_blast_radius=0,
    )


def test_decide_approval_action_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        decide_approval(123, AutonomyTier.FULL)  # type: ignore[arg-type]
    assert str(ei.value) == "action must be a PendingAction, not int"


def test_decide_approval_tier_message_is_exact() -> None:
    with pytest.raises(TypeError) as ei:
        decide_approval(_benign_action(), 123)  # type: ignore[arg-type]
    assert str(ei.value) == "tier must be an AutonomyTier, not int"
