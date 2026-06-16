"""Typed session identity + re-exported determinism seams for the substrate.

What this does
--------------
Defines :class:`SessionId` — the opaque, typed handle for one running
``claude`` CLI session — and re-exports the injectable :class:`Clock` /
:class:`IdGenerator` seams from :mod:`autofirm.org.org_identifiers`. The
substrate models time and identity as *injected inputs*, never ambient: no
module here ever calls ``datetime.now()`` or a UUID factory, so a spawn /
handoff / resume run is a pure function of (state, clock, id-generator, ops).

Why it exists / where it sits
-----------------------------
Lowest layer of :mod:`autofirm.substrate`: the session model, the launcher
contract, and the lifecycle engine all depend on it and nothing depends back.
Reusing the org package's :class:`Clock` / :class:`IdGenerator` (rather than
redefining them) keeps one canonical determinism seam across the platform, so a
test can pin the same :class:`FrozenClock` for an org mutation and the session
it spawns and get one comparable, replayable trail (CLAUDE.md §3.11).

Security / compliance invariants upheld
---------------------------------------
* **Determinism (§3.11):** time + identity are inputs; a session id is allocated
  only via the injected :class:`IdGenerator`, so the Nth spawned session always
  gets the same predictable id in a replay.
* **Typed boundaries (§5.6 validate-at-boundary):** :class:`SessionId` is a
  distinct ``NewType`` so a session id can never be silently passed where a role
  id or artifact id is expected.
"""

from __future__ import annotations

from typing import NewType

from autofirm.org.org_identifiers import (
    Clock,
    FrozenClock,
    IdGenerator,
    SequentialIdGenerator,
)

__all__ = [
    "Clock",
    "FrozenClock",
    "IdGenerator",
    "SequentialIdGenerator",
    "SessionId",
    "session_id_prefix",
]

# A distinct opaque id type for a CLI session. NewType gives static separation
# (a SessionId is not a RoleId) at zero runtime cost; it is just a str at runtime
# and maps directly onto the Claude Code session_id captured from the JSON
# envelope (A5 SYNTHESIS §1: sessions are persisted + resumable by id).
SessionId = NewType("SessionId", str)

# The id-generator prefix for sessions, so a session id is visibly a session id
# in audit trails (e.g. "session-0"). Kept here as the single definition.
session_id_prefix = "session"
