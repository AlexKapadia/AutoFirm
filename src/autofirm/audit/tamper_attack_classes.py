"""The enumerated tamper-attack classes the E5 bake-off must detect.

What this does
--------------
Defines the canonical list of attack classes both candidates are tested against,
so "tamper-detection completeness" (``experiments.md`` E5 metric) is measured over
one shared, named enumeration rather than ad-hoc cases. Each class names a concrete
adversary action against a stored log:

* ``BIT_FLIP``   -- alter the content of an existing entry in place.
* ``REORDER``    -- swap the position of two existing entries.
* ``INSERT``     -- splice a forged entry into the middle of the log.
* ``DELETE``     -- remove an existing middle entry.
* ``TRUNCATE``   -- drop a suffix of entries committed BEFORE a Signed Tree Head.
* ``REPLAY``     -- duplicate an existing entry (re-append a past event).

Why it exists / where it sits
-----------------------------
A6.2 (src 05, Ma-Tsudik) explicitly names truncation and delayed detection as the
attacks a naive chain misses; the bake-off must therefore enumerate truncation and
replay alongside the in-place edits. Sharing this enum keeps the A-vs-B comparison
honest (identical attack set, identical conditions).

Security / compliance invariants upheld
---------------------------------------
Pure data; no side effects. The detection logic lives in each candidate's
verifier; this module only NAMES the adversary's moves.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["TamperAttackClass"]


class TamperAttackClass(StrEnum):
    """The named tamper attacks the E5 metric scores for completeness."""

    BIT_FLIP = "bit_flip"  # alter an existing entry's content in place
    REORDER = "reorder"  # swap two existing entries' positions
    INSERT = "insert"  # splice a forged entry mid-log
    DELETE = "delete"  # remove a middle entry
    TRUNCATE = "truncate"  # drop a suffix committed before an STH (A6.2 src 05)
    REPLAY = "replay"  # duplicate/re-append a past entry
