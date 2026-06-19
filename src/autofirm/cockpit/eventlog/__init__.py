"""Cockpit event log: the shared append-only NDJSON record of cockpit activity.

One :class:`CockpitEvent` per line, newline-delimited, with a monotonic sequence number,
an injected-clock timestamp, provenance URI, and a never-elevated taint flag
(cockpit-research/PLAN.md §2). It is the single source both the live TUI tail and the
deferred web view consume, and a natural audit artifact. Fail-closed and append-only: a
malformed event is refused (raised), never silently dropped — a dropped event is an audit
hole; a prior line is never rewritten. Sensitive finance data is never written here, only
provenance URIs and non-secret summaries.

Status: C0 bootstrap — the event contract, writer, tailer, and replay reader land in gate C2.
"""

from __future__ import annotations
