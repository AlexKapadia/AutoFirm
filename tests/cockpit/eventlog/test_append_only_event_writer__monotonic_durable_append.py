"""AppendOnlyEventWriter: strictly-increasing seq, persisted resume, never-rewrite, fsync.

These are the C2 mutation-risk targets (brief item 1): monotonic seq, resume-after-reopen with
no reset / off-by-one, byte-identical prior lines after later appends, and durability.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from autofirm.cockpit.eventlog.append_only_event_writer import AppendOnlyEventWriter
from autofirm.cockpit.eventlog.cockpit_event_contract import (
    CockpitEvent,
    CockpitEventDecodeError,
    CockpitEventKind,
)
from autofirm.cockpit.eventlog.event_log_reader import read_all

_START = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)


class _StepClock:
    """A deterministic injected clock: returns START + n*step on each call (no wall-clock)."""

    def __init__(self) -> None:
        self._n = 0

    def now(self) -> datetime:
        value = _START + timedelta(seconds=self._n)
        self._n += 1
        return value


def _append(writer: AppendOnlyEventWriter, clock: _StepClock, source: str) -> CockpitEvent:
    return writer.append(
        CockpitEventKind.FRONT_DOOR_REQUEST, source, {"s": source}, now=clock.now()
    )


def test_fresh_writer_starts_at_seq_zero(tmp_path: Path) -> None:
    writer = AppendOnlyEventWriter(tmp_path / "log.ndjson")
    assert writer.next_seq == 0


def test_seq_strictly_increases_within_one_writer(tmp_path: Path) -> None:
    writer = AppendOnlyEventWriter(tmp_path / "log.ndjson")
    clock = _StepClock()
    seqs = [_append(writer, clock, f"e{i}").seq for i in range(5)]
    assert seqs == [0, 1, 2, 3, 4]  # boundary-exact: no gaps, no repeats, starts at 0
    assert writer.next_seq == 5


def test_seq_continues_after_reopen_with_no_reset_or_off_by_one(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    clock = _StepClock()
    first = AppendOnlyEventWriter(path)
    _append(first, clock, "a")  # seq 0
    _append(first, clock, "b")  # seq 1

    reopened = AppendOnlyEventWriter(path)
    assert reopened.next_seq == 2  # resumes at last_seq + 1 (not 0, not 1, not 3)
    third = _append(reopened, clock, "c")
    assert third.seq == 2
    assert [e.seq for e in read_all(path)] == [0, 1, 2]


def test_prior_lines_are_byte_identical_after_later_appends(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    clock = _StepClock()
    writer = AppendOnlyEventWriter(path)
    _append(writer, clock, "a")
    prefix_before = path.read_bytes()
    _append(writer, clock, "b")
    after = path.read_bytes()
    # the new write only APPENDS: the original bytes are an unmodified prefix.
    assert after.startswith(prefix_before)
    assert len(after) > len(prefix_before)


def test_append_is_durable_and_immediately_readable(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    clock = _StepClock()
    writer = AppendOnlyEventWriter(path)
    event = _append(writer, clock, "a")
    # an independent reader sees the flushed+fsync'd event without the writer being closed.
    replayed = read_all(path)
    assert len(replayed) == 1
    assert replayed[0] == event


def test_injected_clock_is_the_only_time_source(tmp_path: Path) -> None:
    writer = AppendOnlyEventWriter(tmp_path / "log.ndjson")
    fixed = datetime(2030, 2, 2, 2, 2, 2, tzinfo=UTC)
    event = writer.append(CockpitEventKind.ORG_CHANGED, "src", {}, now=fixed)
    assert event.recorded_at == fixed  # exactly the injected instant, no wall-clock drift


def test_resume_ignores_blank_tail_lines(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    clock = _StepClock()
    writer = AppendOnlyEventWriter(path)
    _append(writer, clock, "a")  # seq 0
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n   \n")  # stray blank tail lines
    reopened = AppendOnlyEventWriter(path)
    assert reopened.next_seq == 1  # blank lines ignored; resumes from the real last seq


def test_empty_existing_file_resumes_at_zero(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    path.write_text("", encoding="utf-8")
    assert AppendOnlyEventWriter(path).next_seq == 0


def test_only_whitespace_file_resumes_at_zero(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    path.write_text("\n  \n", encoding="utf-8")
    assert AppendOnlyEventWriter(path).next_seq == 0


def test_corrupt_last_line_fails_closed_on_resume(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    path.write_text("{not valid json}\n", encoding="utf-8")
    with pytest.raises(CockpitEventDecodeError):
        AppendOnlyEventWriter(path)  # never guesses a seq from an unreadable log
