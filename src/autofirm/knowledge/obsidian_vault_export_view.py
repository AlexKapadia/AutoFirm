"""Read-only Obsidian markdown projection of the shared-knowledge store (W2/B2).

What this does
--------------
Renders the live shared-knowledge entries as Obsidian-flavoured markdown notes with
``[[backlinks]]`` -- a free human-navigable backlink graph over the authoritative
store (folder 06 of B2). This is a PURE, ONE-WAY projection: it READS a backend
snapshot and RETURNS markdown strings. There is deliberately NO function here that
parses markdown back into entries, writes to the backend, or imports a vault --
the store is the single source of truth (CQRS), the vault is a regenerable view.

The absence of an import path is a SECURITY control, not an omission: a writable
Obsidian round-trip would be an untrusted ingestion surface (anyone who edits a
markdown file could inject a poisoned "fact" into the authoritative store). By
exposing read-only rendering only, this module cannot be the vector for that
write-back, and a test asserts the import path does not exist.

Why it exists / where it sits
------------------------------
Per ``docs/research/B2-shared-knowledge-graph/README.md`` design implication: the
markdown projection is read-only and regenerable; the graph store stays the source
of truth. This module imports ONLY the backend Protocol and the contract -- it does
not touch the assembler or any model.

Security / compliance invariants upheld
---------------------------------------
* **One-way only (§5.6, B6):** no write-back / import API exists; the projection
  cannot be used to inject into the authoritative store.
* **Taint surfaced, not hidden:** each rendered note shows the entry's
  ``origin`` (trusted/untrusted) so a human reviewer sees provenance at a glance.
* **Determinism (§3.11):** rendering is a pure function of the live snapshot in
  insertion order -- identical store -> identical markdown.
"""

from __future__ import annotations

from autofirm.knowledge.knowledge_graph_backend_protocol import KnowledgeGraphBackend
from autofirm.knowledge.shared_knowledge_contract import SharedKnowledgeEntry

__all__ = [
    "render_entry_note",
    "render_vault",
]


def render_entry_note(entry: SharedKnowledgeEntry) -> str:
    """Render ONE live entry as an Obsidian markdown note with a subject backlink.

    The note title is the entry label; the subject is a ``[[wikilink]]`` so Obsidian
    builds a backlink graph anchored on entities (LOCAL/entity-anchored navigation).
    The taint origin is surfaced explicitly so a human reviewer sees at a glance
    whether the value came from a trusted principal or untrusted data.
    """
    invalid = entry.invalid_at.isoformat() if entry.invalid_at is not None else "—"
    lineage = ", ".join(f"[[{src}]]" for src in entry.provenance.derived_from) or "—"
    return (
        f"# {entry.label}\n\n"
        f"**Subject:** [[{entry.subject}]]\n\n"  # backlink: entity-anchored navigation
        f"**Origin (taint):** {entry.origin.value}\n\n"  # surface provenance to the reviewer
        f"**Written by:** {entry.provenance.written_by} "
        f"(provider: {entry.provenance.source_provider})\n\n"
        f"**Valid:** {entry.valid_at.isoformat()} → {invalid}\n\n"
        f"**Derived from:** {lineage}\n\n"
        f"{entry.description}\n\n"
        f"> {entry.value}\n"
    )


def render_vault(backend: KnowledgeGraphBackend) -> dict[str, str]:
    """Render the live store as a ``{filename: markdown}`` vault (read-only snapshot).

    Reads ONLY the live records (``all_live``) from the backend and renders each to a
    note. Returns a mapping the caller may write to disk -- this function performs no
    I/O itself and has no path back INTO the store (one-way projection). Filenames
    are derived deterministically from the entry id so the snapshot is reproducible.
    """
    vault: dict[str, str] = {}
    for entry in backend.all_live():
        # Entry-id-derived filename keeps the projection deterministic and 1:1 with
        # the live record it came from (no merge/collision logic = no hidden state).
        vault[f"{entry.entry_id}.md"] = render_entry_note(entry)
    return vault
