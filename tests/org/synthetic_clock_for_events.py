"""A single fixed timestamp for audit-event construction in unit tests.

Keeps event-construction tests deterministic and free of ambient time, so an
asserted trail is reproducible (CLAUDE.md §3.11). Synthetic only.
"""

from __future__ import annotations

from datetime import UTC, datetime

FIXED_TS = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
