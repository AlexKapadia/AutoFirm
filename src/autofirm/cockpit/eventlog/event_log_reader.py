"""The cockpit event-log reader: full replay and incremental tail (fail-closed on corruption).

What this does
--------------
Provides two pure read functions over an NDJSON cockpit event log:
:func:`read_all` (replay every event in order) and :func:`tail` (every event with ``seq``
greater than a caller-held cursor, for an incremental "what's new since I last looked?" poll).
A missing file is tolerated (returns empty). A malformed line is NOT tolerated — it raises
:class:`~autofirm.cockpit.eventlog.cockpit_event_contract.CockpitEventDecodeError` with the
offending line number, because silently skipping a bad line would hide an audit hole.

Why it exists / where it sits
-----------------------------
Both the live TUI tail and a deferred replay/audit pass read the log through this one seam, so
"how the log is read" lives in one mutation-tested place. Sits in the eventlog layer above the
event contract; depends only on stdlib and the contract.

Security / compliance invariants upheld
---------------------------------------
* **No silent corruption (CLAUDE.md §5.6):** a malformed line raises with its line number; a
  bad event is never dropped on the floor.
* **Missing-file tolerance, not error-swallowing:** an absent log is an empty history (a fresh
  cockpit), distinct from a present-but-corrupt log, which fails closed.
* **Pure reads:** the functions never write, lock, or mutate the file — read-only by design.
"""

from __future__ import annotations

import os
from pathlib import Path

from autofirm.cockpit.eventlog.cockpit_event_contract import (
    CockpitEvent,
    CockpitEventDecodeError,
)

__all__ = ["read_all", "tail"]

_ENCODING = "utf-8"


def read_all(path: str | os.PathLike[str]) -> tuple[CockpitEvent, ...]:
    """Replay every event in ``path`` in file order (empty for a missing file).

    Args:
        path: The NDJSON event-log file.

    Returns:
        Every recorded :class:`CockpitEvent`, in the order written.

    Raises:
        CockpitEventDecodeError: If any non-blank line cannot be parsed — carries the line
            number so the corrupt row is locatable (fail-closed, never skipped).
    """
    file_path = Path(path)
    if not file_path.exists():
        return ()  # a missing log is an empty history, not an error
    events: list[CockpitEvent] = []
    with file_path.open("r", encoding=_ENCODING) as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                # a blank tail line (trailing newline) carries no event; skip only EMPTY
                # lines — any non-blank line MUST parse or the read fails closed below.
                continue
            try:
                events.append(CockpitEvent.from_ndjson_line(line))
            except CockpitEventDecodeError as exc:
                # fail-closed: surface WHERE the corruption is; never silently drop it.
                raise CockpitEventDecodeError(f"line {line_number}: {exc}") from exc
    return tuple(events)


def tail(path: str | os.PathLike[str], *, last_seq: int) -> tuple[CockpitEvent, ...]:
    """Return every event in ``path`` whose ``seq`` is strictly greater than ``last_seq``.

    The incremental-poll seam: a caller holds the highest ``seq`` it has already seen and asks
    for everything newer. A missing file yields an empty tuple.

    Args:
        path: The NDJSON event-log file.
        last_seq: The highest ``seq`` the caller has already consumed.

    Returns:
        The events with ``seq > last_seq``, in file order.

    Raises:
        CockpitEventDecodeError: If the log is present but contains a malformed line.
    """
    return tuple(event for event in read_all(path) if event.seq > last_seq)
