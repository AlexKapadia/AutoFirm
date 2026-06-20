"""The cockpit event contract: one frozen event + its deterministic NDJSON round-trip.

What this does
--------------
Defines :class:`CockpitEventKind` (the closed set of cockpit event kinds), :class:`CockpitEvent`
(one immutable, validated event: ``seq``, ``recorded_at``, ``kind``, ``source``, ``payload``),
and :class:`CockpitEventDecodeError` (raised on a malformed line). :class:`CockpitEvent` knows
how to serialise itself to a single deterministic NDJSON line and parse one back EXACTLY —
``from_ndjson_line(e.to_ndjson_line()) == e`` for every valid event.

Why it exists / where it sits
-----------------------------
The append-only writer and the replay reader both speak this one shape, so the on-disk log is
a single, replayable, audit-grade artifact. Keeping the (de)serialisation on the event itself
(rather than in the writer) means there is exactly one encoding and one decoder to mutation-
test. Sits at the bottom of the eventlog layer; depends only on stdlib.

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed construction (CLAUDE.md §5.6):** a negative ``seq``, a naive (tz-unaware)
  timestamp, a blank ``source``, or a non-string payload key/value is refused — a malformed
  event cannot exist and reach the log.
* **No silent corruption (§5.6):** :meth:`from_ndjson_line` raises :class:`CockpitEventDecodeError`
  on any malformed line; a bad line is never silently skipped (a dropped event is an audit hole).
* **Deterministic encoding (§3.11):** keys are emitted sorted with fixed separators, so the
  same event always produces byte-identical NDJSON (replayable, diffable).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType

__all__ = ["CockpitEvent", "CockpitEventDecodeError", "CockpitEventKind"]

_REQUIRED_FIELDS = ("seq", "recorded_at", "kind", "source", "payload")


class CockpitEventDecodeError(ValueError):
    """Raised when an NDJSON line cannot be parsed into a valid :class:`CockpitEvent`.

    Subclasses :class:`ValueError` so a caller can catch it specifically. Carries a clear,
    line-context message so a corrupt log is diagnosable (fail-closed, never silent).
    """


class CockpitEventKind(StrEnum):
    """The closed set of cockpit event kinds (one applies to every recorded event).

    A closed set keeps the log auditable and lets a reader reason about every kind. Values
    are lower-cased, stable strings written verbatim into the NDJSON ``kind`` field.
    """

    FRONT_DOOR_REQUEST = "front_door_request"  # a human request crossed the front door
    ORG_CHANGED = "org_changed"  # a role was hired / fired / rescoped
    SPEND_RECORDED = "spend_recorded"  # a cost row was appended to the ledger
    KILL_SWITCH_OBSERVED = "kill_switch_observed"  # the kill-switch epoch was sampled


@dataclass(frozen=True, slots=True)
class CockpitEvent:
    """One immutable cockpit event, with a deterministic NDJSON round-trip.

    Attributes:
        seq: The monotonic, strictly-increasing sequence number (``>= 0``).
        recorded_at: When the event was recorded (tz-aware; injected clock, never wall-clock).
        kind: Which :class:`CockpitEventKind` this event is.
        source: A non-blank provenance string (who/what produced the event).
        payload: A string→string mapping of non-secret summary fields (wrapped read-only).
    """

    seq: int
    recorded_at: datetime
    kind: CockpitEventKind
    source: str
    payload: Mapping[str, str]

    def __post_init__(self) -> None:
        """Validate fail-closed, then freeze ``payload`` into a read-only proxy.

        Raises:
            TypeError: If ``seq`` is not an ``int`` (a ``bool`` is rejected), ``kind`` is not a
                :class:`CockpitEventKind`, or any payload key/value is not a ``str``.
            ValueError: If ``seq`` is negative, ``recorded_at`` is naive, or ``source`` is blank.
        """
        # fail-closed: a bool is an int subclass but is never a valid sequence number.
        if not isinstance(self.seq, int) or isinstance(self.seq, bool):
            raise TypeError("seq must be an int")
        if self.seq < 0:
            raise ValueError("seq must be >= 0")
        if not isinstance(self.kind, CockpitEventKind):
            raise TypeError("kind must be a CockpitEventKind")
        # fail-closed: a naive timestamp is ambiguous across zones — refuse it so every
        # logged instant is unambiguously anchored (mirrors the org FrozenClock rule).
        if self.recorded_at.tzinfo is None:
            raise ValueError("recorded_at must be timezone-aware")
        if not self.source.strip():
            raise ValueError("source must be a non-empty provenance string")
        for key, value in self.payload.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise TypeError("payload keys and values must both be str")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))

    def to_ndjson_line(self) -> str:
        """Serialise to one deterministic NDJSON line (no trailing newline).

        Keys are emitted sorted with fixed separators so the same event always produces the
        same bytes; the timestamp is ISO-8601 (round-trips exactly via ``fromisoformat``).
        """
        obj = {
            "seq": self.seq,
            "recorded_at": self.recorded_at.isoformat(),
            "kind": self.kind.value,
            "source": self.source,
            "payload": dict(self.payload),
        }
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_ndjson_line(cls, line: str) -> CockpitEvent:
        """Parse one NDJSON line back into a :class:`CockpitEvent` (fail-closed exact round-trip).

        Raises:
            CockpitEventDecodeError: If the line is not valid JSON, is not a JSON object, is
                missing a required field, or carries a value of the wrong type / shape.
        """
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise CockpitEventDecodeError(f"not valid JSON: {exc}") from exc
        if not isinstance(obj, dict):
            raise CockpitEventDecodeError(f"expected a JSON object, got {type(obj).__name__}")
        for field in _REQUIRED_FIELDS:
            if field not in obj:
                raise CockpitEventDecodeError(f"missing required field {field!r}")
        return cls(
            seq=_decode_seq(obj["seq"]),
            recorded_at=_decode_timestamp(obj["recorded_at"]),
            kind=_decode_kind(obj["kind"]),
            source=_decode_source(obj["source"]),
            payload=_decode_payload(obj["payload"]),
        )


def _decode_seq(value: object) -> int:
    """Decode ``seq``: must be a real int (a bool or non-int is refused)."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise CockpitEventDecodeError(f"seq must be an int, got {type(value).__name__}")
    return value


def _decode_timestamp(value: object) -> datetime:
    """Decode ``recorded_at``: must be an ISO-8601 string parseable to a datetime."""
    if not isinstance(value, str):
        raise CockpitEventDecodeError(f"recorded_at must be a str, got {type(value).__name__}")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise CockpitEventDecodeError(f"recorded_at is not ISO-8601: {value!r}") from exc


def _decode_kind(value: object) -> CockpitEventKind:
    """Decode ``kind``: must be a known :class:`CockpitEventKind` value."""
    if not isinstance(value, str):
        raise CockpitEventDecodeError(f"kind must be a str, got {type(value).__name__}")
    try:
        return CockpitEventKind(value)
    except ValueError as exc:
        raise CockpitEventDecodeError(f"unknown event kind {value!r}") from exc


def _decode_source(value: object) -> str:
    """Decode ``source``: must be a string (blankness is enforced by construction)."""
    if not isinstance(value, str):
        raise CockpitEventDecodeError(f"source must be a str, got {type(value).__name__}")
    return value


def _decode_payload(value: object) -> dict[str, str]:
    """Decode ``payload``: must be a JSON object of string→string (refuse other shapes)."""
    if not isinstance(value, dict):
        raise CockpitEventDecodeError(f"payload must be an object, got {type(value).__name__}")
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise CockpitEventDecodeError("payload keys and values must both be strings")
    return dict(value)
