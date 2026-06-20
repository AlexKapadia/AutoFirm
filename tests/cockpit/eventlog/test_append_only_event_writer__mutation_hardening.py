"""Mutation-killing assertions for the append-only event writer (CLAUDE.md §3.6).

Why this file exists
--------------------
The behavioural writer suite proves monotonic, durable append but never pins the *encoding*
the log is opened with. mutmut mutates the ``_ENCODING = "utf-8"`` constant to ``None`` (and
under a UTF-8-mode interpreter ``open(encoding=None)`` is behaviourally identical to UTF-8, so
a content round-trip cannot distinguish them). These tests pin the encoding ARGUMENT passed to
``open`` with ``== "utf-8"`` -- a platform-independent kill for the ``None`` mutant -- and add
a byte-level UTF-8 determinism assertion on the persisted log.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from autofirm.cockpit.eventlog.append_only_event_writer import AppendOnlyEventWriter
from autofirm.cockpit.eventlog.cockpit_event_contract import CockpitEventKind

_TS = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)


def _spy_on_open(monkeypatch) -> list[object]:  # type: ignore[no-untyped-def]
    """Record the ``encoding`` kwarg of every ``Path.open`` call; delegate to the real open."""
    seen: list[object] = []
    real_open = Path.open

    def spy(self: Path, *args: object, **kwargs: object) -> object:
        seen.append(kwargs.get("encoding"))
        return real_open(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "open", spy)
    return seen


def test_append_opens_log_with_explicit_utf8(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    seen = _spy_on_open(monkeypatch)
    writer = AppendOnlyEventWriter(tmp_path / "log.ndjson")
    writer.append(CockpitEventKind.ORG_CHANGED, "org://engine", {"k": "v"}, now=_TS)
    assert seen, "writer never opened the log file"
    # Every open must use explicit UTF-8; the `_ENCODING = None` mutant records None here.
    assert all(enc == "utf-8" for enc in seen)


def test_resume_reopen_reads_log_with_explicit_utf8(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "log.ndjson"
    AppendOnlyEventWriter(path).append(
        CockpitEventKind.SPEND_RECORDED, "ledger", {"i": "0"}, now=_TS
    )
    # Now reopen on the EXISTING file: this exercises the read-side use of _ENCODING.
    seen = _spy_on_open(monkeypatch)
    reopened = AppendOnlyEventWriter(path)
    assert reopened.next_seq == 1
    assert seen, "reopen never read the existing log"
    assert all(enc == "utf-8" for enc in seen)


def test_persisted_log_is_utf8_bytes_for_non_ascii(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    writer = AppendOnlyEventWriter(path)
    event = writer.append(
        CockpitEventKind.FRONT_DOOR_REQUEST,
        "café://wösch",
        {"naïve": "résumé"},
        now=_TS,
    )
    # The non-ASCII fields land on disk as their UTF-8 byte sequences (e.g. "é" -> b"\xc3\xa9"),
    # independent of the process locale -> proves the explicit utf-8 encoding. (Newline
    # translation in text mode is irrelevant to the encoding, so we check content bytes.)
    raw = path.read_bytes()
    assert "café://wösch".encode() in raw
    assert "résumé".encode() in raw
    assert "naïve".encode() in raw
    # and it round-trips back to the exact event via a UTF-8 decode.
    assert event.to_ndjson_line() == raw.decode("utf-8").strip()
