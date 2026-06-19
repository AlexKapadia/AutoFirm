"""The model-egress kill-switch epoch: a fail-closed global halt token (C7).

What this does
--------------
Defines :class:`KillSwitchEpoch` — the frozen value the invocation contract and
the selection policy carry to prove egress is permitted *right now*. An epoch is a
monotonic version counter plus a ``tripped`` flag. When ``tripped`` is ``True`` the
global kill-switch is engaged and **no** model call may proceed; the deterministic
selection policy and the HTTP client both refuse fail-closed on a tripped epoch
(``threat-model`` C7). The version lets a relaunch tell a stale (pre-trip) token
from a fresh (post-reset) one without trusting wall-clock.

Why it exists / where it sits
-----------------------------
``data-contracts.md`` §7 types ``ModelInvocationRequest.kill_switch_token`` as
``KillSwitchEpoch`` and ADR-003 makes a single kill-switch a first-class control on
the one audited egress chokepoint. Keeping the type here (the lowest gateway layer,
beside :mod:`model_reference`) means every gateway component shares one definition
of "is egress halted?" rather than re-encoding the flag as an ad-hoc bool that a
caller could forget to check.

Security / compliance invariants upheld (CLAUDE.md §5.6)
-------------------------------------------------------
* **Fail-closed halt (§5.6, C7):** :meth:`require_egress_permitted` raises when the
  epoch is tripped — a single flag halts all external model calls.
* **Monotonic, non-negative version:** a negative epoch version is refused at
  construction (an ambiguous/forged epoch is never accepted).
* **Immutable:** the epoch is frozen — a token is a value snapshot, not mutable
  state a caller could flip after a check (no time-of-check/time-of-use gap).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = ["KillSwitchEngaged", "KillSwitchEpoch"]


class KillSwitchEngaged(RuntimeError):
    """Raised when egress is attempted while the kill-switch epoch is tripped.

    Carries only the epoch version (non-secret) so the refusal is auditable without
    exposing any prompt, credential, or model content.
    """


class KillSwitchEpoch(BaseModel):
    """An immutable global-egress permission token (version + tripped flag, C7).

    A request carries the epoch it was authorised under; the policy and the HTTP
    client both call :meth:`require_egress_permitted` before any egress and refuse
    fail-closed when ``tripped`` is set.
    """

    model_config = ConfigDict(frozen=True)

    version: int  # monotonic counter; a reset/re-arm bumps it (distinguishes stale tokens)
    tripped: bool = False  # True => global halt; egress is refused fail-closed (C7)

    @field_validator("version")
    @classmethod
    def _version_non_negative(cls, value: int) -> int:
        # fail-closed: a negative epoch version is a malformed/forged token — refuse
        # it rather than treat an ambiguous version as a valid (untripped) epoch.
        if value < 0:
            raise ValueError("kill-switch epoch version must be >= 0")
        return value

    def require_egress_permitted(self) -> None:
        """Return ``None`` if egress is allowed; raise :class:`KillSwitchEngaged` if not.

        The single guard every egress path calls first. A tripped epoch halts ALL
        model calls (fail-closed, C7) — the refusal names only the epoch version.
        """
        # fail-closed: a tripped kill-switch refuses every egress, no exceptions.
        if self.tripped:
            raise KillSwitchEngaged(
                f"model egress kill-switch is engaged (epoch version {self.version})"
            )
