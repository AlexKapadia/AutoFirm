"""Fail-closed tests for the kill-switch epoch (C7): a tripped epoch halts egress.

Kills mutants on the trip check and the non-negative version validator.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from autofirm.modelgateway.kill_switch_epoch import KillSwitchEngaged, KillSwitchEpoch


@pytest.mark.unit
@pytest.mark.security
def test_tripped_epoch_refuses_egress() -> None:
    with pytest.raises(KillSwitchEngaged, match="kill-switch is engaged"):
        KillSwitchEpoch(version=4, tripped=True).require_egress_permitted()


@pytest.mark.unit
def test_untripped_epoch_permits_egress() -> None:
    # an untripped epoch returns None (does not raise) — egress proceeds.
    assert KillSwitchEpoch(version=0).require_egress_permitted() is None


@pytest.mark.unit
def test_epoch_refuses_negative_version() -> None:
    with pytest.raises(ValidationError, match=">= 0"):
        KillSwitchEpoch(version=-1)


@pytest.mark.unit
def test_epoch_is_frozen() -> None:
    e = KillSwitchEpoch(version=1)
    with pytest.raises(ValidationError):
        e.tripped = True  # type: ignore[misc]
