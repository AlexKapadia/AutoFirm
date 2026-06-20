"""The cockpit-owned production clock: the single real wall-clock in the cockpit.

What this does
--------------
Defines :class:`SystemClock`, a concrete :class:`~autofirm.org.org_identifiers.Clock` whose
``now()`` returns the current timezone-aware UTC instant via ``datetime.now(UTC)``. This is
the ONLY place in the cockpit that reads the real wall-clock; every other module takes a
``Clock`` so it can be pinned. Tests inject a ``FrozenClock`` instead and never touch this.

Why it exists / where it sits
-----------------------------
The composer defaults to this clock so a real run stamps events with real time, while a test
substitutes a deterministic clock for byte-identical, replayable timestamps (CLAUDE.md §3.11).
Keeping the wall-clock in exactly one swappable module is what makes the rest of the cockpit
deterministic. Sits in the composition layer; depends only on stdlib and the Clock Protocol.

Security / compliance invariants upheld
---------------------------------------
* **Timezone-aware, never naive (CLAUDE.md §3.11):** ``now()`` returns a UTC-anchored instant,
  so every cockpit timestamp is unambiguous across zones (the event contract refuses naive ones).
* **Single ambient seam:** ambient time enters the cockpit here and nowhere else, so a test can
  make the whole system deterministic by injecting one clock.
"""

from __future__ import annotations

from datetime import UTC, datetime

__all__ = ["SystemClock"]


class SystemClock:
    """The production :class:`~autofirm.org.org_identifiers.Clock` over the real wall-clock.

    Implements the org ``Clock`` Protocol structurally (it exposes ``now()``), so it can be
    injected anywhere a ``Clock`` is expected. Holds no state.
    """

    __slots__ = ()

    def now(self) -> datetime:
        """Return the current instant as a timezone-aware UTC ``datetime``."""
        return datetime.now(UTC)
