"""Synthetic fixtures + a recording audit sink for the access-layer test suites.

Provides a deterministic clock, an in-memory audit sink that records every event
the broker emits (so tests can assert on issuance/deny records AND scan them for
secret leakage), and Hypothesis strategies for tenants/operations/identifiers.
Synthetic only -- no network, no DB, no real secrets.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hypothesis import strategies as st

from autofirm.access.credential_scope_contract import Operation

# A fixed UTC instant for deterministic issued_at/expires_at assertions.
FIXED_NOW = datetime(2026, 6, 16, 12, 0, 0, tzinfo=UTC)


class AdvancingClock:
    """A deterministic clock that returns ``start`` then advances by ``step`` per call."""

    def __init__(self, start: datetime = FIXED_NOW, step: timedelta = timedelta(0)) -> None:
        """Seed at ``start``, advancing ``step`` per ``now()`` call."""
        self._current = start
        self._step = step

    def now(self) -> datetime:
        value = self._current
        self._current = self._current + self._step
        return value


class RecordingAuditSink:
    """An append-only audit sink that keeps every event for inspection in tests.

    Mirrors the production contract: ``append`` only ever grows the list; the test
    suite asserts on issuance/deny events and (critically) scans every recorded
    value to prove no secret material ever lands in the audit.
    """

    def __init__(self) -> None:
        """Start with an empty append-only event list."""
        self.events: list[dict[str, str]] = []

    def append(self, event: dict[str, str]) -> None:
        self.events.append(dict(event))


# --- Hypothesis strategies (synthetic, bounded, varied) ---------------------

# Identifiers: non-empty, no leading/trailing whitespace-only strings.
identifier_strategy = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126),
    min_size=1,
    max_size=24,
)

operation_strategy = st.sampled_from(list(Operation))

operation_set_strategy = st.frozensets(operation_strategy, min_size=1)

# Two distinct tenant ids, for cross-tenant denial properties.
distinct_tenants_strategy = st.lists(identifier_strategy, min_size=2, max_size=2, unique=True)
