"""The typed definition of one recurring beat: a name, an interval, a callback.

What this does
--------------
Defines :class:`BeatDefinition` — the immutable specification of a single
recurring cadence: a unique ``name``, a strictly-positive ``interval_seconds``,
and the zero-argument ``callback`` fired on each due tick. Construction is
fail-closed: a blank name or a non-positive interval is refused, so a beat that
could never sensibly fire (no name to dedupe on, or an interval of 0 / negative
that would fire every instant or never) can never be registered.

Why it exists / where it sits
-----------------------------
This is the lowest layer of ``autofirm.heartbeat``: the scheduler holds a set of
these and nothing depends back on the scheduler from here. Separating the
*definition* (validated data) from the *scheduling* (the due-time engine) keeps
each file single-responsibility and lets the validation be property-tested on its
own.

Security / compliance invariants upheld
---------------------------------------
* **Fail-closed registration (CLAUDE.md §5.6):** a non-positive interval or blank
  name is refused at construction — a mis-specified beat never reaches the
  scheduler. Duplicate-name prevention lives in the scheduler (it owns the set).
"""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = ["BeatDefinition"]


class BeatDefinition(BaseModel):
    """An immutable specification of one recurring heartbeat.

    ``callback`` is a zero-argument side-effecting check fired on each due tick
    (e.g. "run the North Star alignment review"). It is intentionally opaque to
    this layer — the scheduler only decides *when* to fire it, never *what* it
    does. The model is frozen so a registered beat's contract cannot mutate.
    """

    # arbitrary_types_allowed: a callback is a plain Python callable, not a
    # pydantic-modelable type; we still validate the fields that guard scheduling.
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    name: str  # unique cadence name (the scheduler dedupes on this)
    interval_seconds: float  # strictly positive period between fires
    callback: Callable[[], None]  # the zero-arg check fired on each due tick

    @field_validator("name")
    @classmethod
    def _name_non_empty(cls, value: str) -> str:
        # fail-closed: a beat with no name cannot be deduplicated or referenced.
        if not value.strip():
            raise ValueError("beat name must be non-empty")
        return value

    @field_validator("interval_seconds")
    @classmethod
    def _interval_strictly_positive(cls, value: float) -> float:
        # fail-closed: a 0 interval would be "due every instant" (a busy-loop) and
        # a negative interval is meaningless — only a positive period is valid.
        if value <= 0:
            raise ValueError("interval_seconds must be strictly positive")
        return value
