"""The frozen cockpit configuration value (no secrets ever stored here).

What this does
--------------
Defines :class:`CockpitConfig` — the immutable, validated bundle of the few inputs the
cockpit composition root needs to assemble a runnable cockpit: where the append-only event
log lives, the single ISO-4217 currency every spend figure is denominated in, an optional
budget ceiling, an optional replay-source override, and an optional kill-switch epoch seed
for the in-memory fake. The operator secret is DELIBERATELY NOT a field — a token must never
enter a value object that could be logged, repr'd, or written into the audit trail.

Why it exists / where it sits
-----------------------------
The composer (:mod:`~autofirm.cockpit.composition.cockpit_composer`) takes one of these and
wires every collaborator from it, so "what the cockpit is configured with" lives in one
typed, validated place rather than scattered keyword arguments. Sits at the bottom of the
composition layer; depends only on the foundation ``Money`` type and the gateway epoch.

Security / compliance invariants upheld
---------------------------------------
* **No secret in config (CLAUDE.md §5.6):** the operator token is not a field — secrets are
  read from the environment at the transport boundary, never carried in a loggable object.
* **Fail-closed validation (§5.6):** a blank or non-uppercase currency is refused at
  construction, so a malformed currency can never reach a money rollup.
* **Immutable (§3.8):** frozen + slots — a configured cockpit cannot be re-pointed after the
  fact, and the object carries no ``__dict__`` to smuggle extra state onto.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from autofirm.foundation.money.money_amount import Money
from autofirm.modelgateway.kill_switch_epoch import KillSwitchEpoch

__all__ = ["CockpitConfig"]


@dataclass(frozen=True, slots=True)
class CockpitConfig:
    """An immutable, validated cockpit configuration (never carries a secret).

    Attributes:
        event_log_path: Where the append-only NDJSON cockpit event log is read/written.
        currency: The single ISO-4217 currency (upper-case, non-blank) every spend figure
            is denominated in; threaded through the spend adapter verbatim.
        budget: An optional budget ceiling; a budget band is classified only when this is a
            strictly-positive ``Money`` (the spend adapter enforces the positivity rule).
        replay_source_path: An optional override the replay path reads from instead of
            ``event_log_path`` (e.g. an archived log); ``None`` means "replay the live log".
        kill_switch_epoch: An optional seed for the in-memory kill-switch fake; ``None``
            means the composer seeds an untripped version-0 epoch.
    """

    event_log_path: Path
    currency: str
    budget: Money | None = None
    replay_source_path: Path | None = None
    kill_switch_epoch: KillSwitchEpoch | None = None

    def __post_init__(self) -> None:
        """Validate the currency fail-closed (non-blank, upper-case ISO-4217 shape).

        Raises:
            ValueError: If ``currency`` is blank/whitespace-only or is not upper-case — a
                malformed currency must never reach a money rollup (fail-closed, §5.6).
        """
        # fail-closed: a blank currency would silently denominate spend in nothing.
        if not self.currency.strip():
            raise ValueError("currency must be a non-empty ISO-4217 code")
        # fail-closed: a lower/mixed-case code (e.g. 'usd') is a caller bug; ISO-4217 codes
        # are upper-case, and Money's minor-unit table is keyed upper-case, so refuse it here
        # rather than fail deeper with a confusing 'unknown currency'.
        if not self.currency.isupper():
            raise ValueError(f"currency must be an upper-case ISO-4217 code, got {self.currency!r}")
