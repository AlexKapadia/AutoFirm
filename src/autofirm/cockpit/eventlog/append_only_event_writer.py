"""The append-only cockpit event writer: durable, monotonic, never-rewriting NDJSON.

What this does
--------------
Defines :class:`AppendOnlyEventWriter` — it appends one :class:`CockpitEvent` per NDJSON line
to a file. It assigns each event a strictly-increasing ``seq`` that PERSISTS across reopen
(on construction it reads the last line's ``seq`` and continues from there), it NEVER rewrites
or truncates an existing line (every write is append-mode), and it flushes then fsyncs after
each write so a recorded event survives a crash. The clock is injected (``now`` is passed in),
so the writer is fully deterministic and makes no wall-clock call.

Why it exists / where it sits
-----------------------------
The cockpit's shared event log must be an append-only, durable audit artifact (a dropped or
rewritten line is an audit hole). Persisting the sequence across reopen is what lets a
relaunched cockpit continue one monotonic stream rather than restarting at 0. Sits in the
eventlog layer above the event contract; depends only on stdlib.

Security / compliance invariants upheld
---------------------------------------
* **Append-only (CLAUDE.md §3.8 / §5.6):** the file is opened in append mode; existing bytes
  are never rewritten or truncated.
* **Durability (§5.6):** every append is flushed then fsynced before returning, so a recorded
  event is on stable storage, not just in a buffer.
* **Monotonic, persisted seq (§3.11):** ``seq`` strictly increases and resumes from the last
  persisted line on reopen — never resets, never collides, no off-by-one.
* **Deterministic (§3.11):** time is an injected input (``now``), never ambient wall-clock.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

from autofirm.cockpit.eventlog.cockpit_event_contract import CockpitEvent, CockpitEventKind

__all__ = ["AppendOnlyEventWriter"]

_ENCODING = "utf-8"


class AppendOnlyEventWriter:
    """Appends cockpit events to an NDJSON file with a persisted, monotonic sequence.

    On construction the writer scans the existing file (if any) for the last event's ``seq``
    and continues from ``seq + 1``, so a reopened writer never resets or collides. The file
    is always opened in append mode and fsync'd, so the log is append-only and durable.
    """

    __slots__ = ("_next_seq", "_path")

    def __init__(self, path: str | os.PathLike[str]) -> None:
        """Bind the writer to ``path`` and resume the sequence from any existing log."""
        self._path = Path(path)
        self._next_seq = self._resume_next_seq()

    @property
    def next_seq(self) -> int:
        """The ``seq`` the next :meth:`append` will assign (the resumed/monotonic cursor)."""
        return self._next_seq

    def append(
        self,
        kind: CockpitEventKind,
        source: str,
        payload: Mapping[str, str],
        *,
        now: datetime,
    ) -> CockpitEvent:
        """Append one event with the next ``seq``; return the fully-built :class:`CockpitEvent`.

        The event is validated by :class:`CockpitEvent` construction (fail-closed), serialised
        to one NDJSON line, appended, flushed, and fsync'd before the cursor advances — so a
        crash mid-write never leaves the in-memory cursor ahead of durable storage.

        Args:
            kind: The event kind to record.
            source: A non-blank provenance string.
            payload: A string→string mapping of non-secret summary fields.
            now: The recording instant (tz-aware), injected by the caller's clock.

        Returns:
            The recorded :class:`CockpitEvent`, carrying the assigned ``seq``.
        """
        event = CockpitEvent(
            seq=self._next_seq,
            recorded_at=now,
            kind=kind,
            source=source,
            payload=payload,
        )
        line = event.to_ndjson_line()
        # append mode: never truncates/rewrites prior lines (append-only invariant).
        with self._path.open("a", encoding=_ENCODING) as handle:
            handle.write(line + "\n")
            handle.flush()  # push out of the Python buffer...
            os.fsync(handle.fileno())  # ...and force the OS to commit to stable storage.
        self._next_seq += 1  # advance only AFTER a durable write (strictly increasing)
        return event

    def _resume_next_seq(self) -> int:
        """Return the next ``seq`` to assign: last persisted ``seq`` + 1, or 0 for a fresh log.

        Reads the last non-blank line of the existing file and parses its ``seq``. A missing
        or empty file resumes at 0. A corrupt last line fails closed (the parse raises), so the
        writer never guesses a sequence from an unreadable log.
        """
        if not self._path.exists():
            return 0
        last_line: str | None = None
        with self._path.open("r", encoding=_ENCODING) as handle:
            for line in handle:
                if line.strip():  # ignore a trailing newline / blank tail line
                    last_line = line
        if last_line is None:
            return 0
        # fail-closed: a malformed last line raises here rather than resuming at a guess.
        return CockpitEvent.from_ndjson_line(last_line).seq + 1
