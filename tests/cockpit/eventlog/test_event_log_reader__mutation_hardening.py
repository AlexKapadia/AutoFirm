"""Mutation-killing assertions for the event-log reader (CLAUDE.md §3.6).

Why this file exists
--------------------
Three reader mutants survive the behavioural suite:
* ``_ENCODING = "utf-8"`` -> ``None`` -- the blank-tail test uses ASCII, and under a UTF-8-mode
  interpreter ``open(encoding=None)`` is identical to UTF-8; killed here by pinning the
  ``encoding`` ARGUMENT of ``open`` with ``== "utf-8"`` (platform-independent).
* ``continue`` -> ``break`` on the blank-line skip -- the existing test puts blank lines only at
  the TAIL, so a ``break`` there changes nothing; killed here with a blank line in the MIDDLE,
  after which a ``break`` would silently drop later events.
* the ``f"line {n}: {exc}"`` string-wrap -- the existing test uses ``match=`` (substring), which
  a wrapped ``"XXline 2: ...XX"`` still satisfies; killed here with an exact ``startswith``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from autofirm.cockpit.eventlog.cockpit_event_contract import (
    CockpitEvent,
    CockpitEventDecodeError,
    CockpitEventKind,
)
from autofirm.cockpit.eventlog.event_log_reader import read_all

_TS = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)


def _event(seq: int) -> CockpitEvent:
    return CockpitEvent(
        seq=seq,
        recorded_at=_TS,
        kind=CockpitEventKind.SPEND_RECORDED,
        source="ledger",
        payload={"i": str(seq)},
    )


def test_read_all_opens_log_with_explicit_utf8(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "log.ndjson"
    path.write_text(_event(0).to_ndjson_line() + "\n", encoding="utf-8")
    seen: list[object] = []
    real_open = Path.open

    def spy(self: Path, *args: object, **kwargs: object) -> object:
        seen.append(kwargs.get("encoding"))
        return real_open(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "open", spy)
    assert [e.seq for e in read_all(path)] == [0]
    assert seen, "read_all never opened the log"
    # The `_ENCODING = None` mutant records None here instead of "utf-8".
    assert all(enc == "utf-8" for enc in seen)


def test_read_all_skips_a_blank_line_in_the_MIDDLE_keeping_later_events(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    # event0, a BLANK line, then event1 -> a `break` on the blank would drop event1.
    path.write_text(
        _event(0).to_ndjson_line() + "\n\n" + _event(1).to_ndjson_line() + "\n",
        encoding="utf-8",
    )
    assert [e.seq for e in read_all(path)] == [0, 1]  # continue (not break) keeps event1


def test_read_all_corruption_message_line_prefix_is_exact(tmp_path: Path) -> None:
    path = tmp_path / "log.ndjson"
    # line 1 valid, line 2 a blank, line 3 corrupt -> message must name line 3 exactly.
    path.write_text(
        _event(0).to_ndjson_line() + "\n\n{garbage}\n",
        encoding="utf-8",
    )
    with pytest.raises(CockpitEventDecodeError) as ei:
        read_all(path)
    # The wrap mutant ("XXline 3: ...XX") starts with "XX" and fails both assertions.
    assert str(ei.value).startswith("line 3: ")
    assert not str(ei.value).startswith("XX")
