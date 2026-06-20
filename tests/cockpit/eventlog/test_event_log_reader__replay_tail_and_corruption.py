"""event_log_reader: replay, incremental tail, missing-file tolerance, fail-closed corruption."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from autofirm.cockpit.eventlog.append_only_event_writer import AppendOnlyEventWriter
from autofirm.cockpit.eventlog.cockpit_event_contract import (
    CockpitEventDecodeError,
    CockpitEventKind,
)
from autofirm.cockpit.eventlog.event_log_reader import read_all, tail

_START = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)


def _write_n(path: Path, n: int) -> AppendOnlyEventWriter:
    writer = AppendOnlyEventWriter(path)
    for i in range(n):
        writer.append(
            CockpitEventKind.SPEND_RECORDED, "ledger", {"i": str(i)},
            now=_START + timedelta(seconds=i),
        )
    return writer


# --------------------------- read_all --------------------------- #


def test_read_all_missing_file_returns_empty(tmp_path: Path) -> None:
    assert read_all(tmp_path / "absent.ndjson") == ()


def test_read_all_replays_every_event_in_order(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    _write_n(path, 4)
    events = read_all(path)
    assert [e.seq for e in events] == [0, 1, 2, 3]
    assert [e.payload["i"] for e in events] == ["0", "1", "2", "3"]


def test_read_all_skips_blank_lines_but_keeps_events(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    _write_n(path, 2)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n   \n")  # blank tail lines carry no event
    assert [e.seq for e in read_all(path)] == [0, 1]


def test_read_all_raises_on_malformed_line_with_line_number(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    _write_n(path, 1)  # line 1 is valid
    with path.open("a", encoding="utf-8") as handle:
        handle.write("{garbage}\n")  # line 2 is corrupt
    with pytest.raises(CockpitEventDecodeError, match="line 2:"):
        read_all(path)


def test_read_all_does_not_silently_skip_a_bad_middle_line(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    path.write_text('{"bad": true}\n', encoding="utf-8")  # missing required fields
    with pytest.raises(CockpitEventDecodeError, match="line 1:"):
        read_all(path)


# --------------------------- tail --------------------------- #


def test_tail_returns_only_events_after_cursor(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    _write_n(path, 5)
    fresh = tail(path, last_seq=2)
    assert [e.seq for e in fresh] == [3, 4]  # strictly greater than 2


def test_tail_cursor_is_exclusive_boundary(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    _write_n(path, 3)
    # last_seq == highest existing seq -> nothing newer.
    assert tail(path, last_seq=2) == ()
    # a cursor below the floor returns everything.
    assert [e.seq for e in tail(path, last_seq=-1)] == [0, 1, 2]


def test_tail_missing_file_returns_empty(tmp_path: Path) -> None:
    assert tail(tmp_path / "absent.ndjson", last_seq=0) == ()


def test_tail_propagates_corruption(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    path.write_text("{nope}\n", encoding="utf-8")
    with pytest.raises(CockpitEventDecodeError):
        tail(path, last_seq=0)
