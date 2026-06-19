"""Read-only one-way projection tests for the Obsidian vault export (W2/B2/§5.6).

Proves teeth (CLAUDE.md §3.6): the projection renders only LIVE entries, surfaces
taint, and -- critically -- has NO import/write-back path. The security claim ("the
vault can never inject into the authoritative store") is asserted structurally: the
module exposes only render functions and no symbol that parses markdown or writes to
the backend. Designed to catch a regression that adds an ingestion surface.
"""

from __future__ import annotations

import inspect

from autofirm.knowledge import obsidian_vault_export_view as view
from autofirm.knowledge.shared_knowledge_contract import TaintOrigin
from tests.knowledge.synthetic_knowledge_fixtures import at_day, make_entry, make_graph


def test_render_entry_note_surfaces_subject_backlink_and_taint() -> None:
    entry = make_entry(entry_id="k1", subject="pricing_model", label="pricing_model",
                       origin=TaintOrigin.UNTRUSTED, value="scraped price claim")
    note = view.render_entry_note(entry)
    assert "[[pricing_model]]" in note  # entity-anchored backlink
    assert "untrusted" in note  # taint surfaced to the human reviewer
    assert "scraped price claim" in note  # the value is shown


def test_render_vault_includes_only_live_entries() -> None:
    g = make_graph()
    g.write(make_entry(entry_id="k1", value="live fact", recorded_at=at_day(1)))
    g.supersede(
        entry_id="k1",
        replacement=make_entry(entry_id="k2", value="new live fact", recorded_at=at_day(6)),
        superseded_at=at_day(6),
    )
    vault = view.render_vault(g)
    # The superseded k1 is NOT projected; only the live k2 is.
    assert set(vault) == {"k2.md"}
    assert "new live fact" in vault["k2.md"]


def test_render_vault_is_deterministic() -> None:
    g = make_graph()
    for i in range(4):
        g.write(make_entry(entry_id=f"k{i}", label=f"f{i}", value=f"fact {i}"))
    assert view.render_vault(g) == view.render_vault(g)


def test_no_write_back_or_import_symbol_exists_one_way_only() -> None:
    # SECURITY: the module's public surface is render-only. There is NO function that
    # parses markdown back into entries or writes to the backend -- the projection
    # cannot be an injection vector into the authoritative store (B6).
    public = set(view.__all__)
    assert public == {"render_entry_note", "render_vault"}
    # No module-level callable hints at ingestion/import/parse/write-back.
    forbidden = ("import", "parse", "load", "ingest", "write_back", "from_markdown", "sync")
    members = {n for n, obj in inspect.getmembers(view, inspect.isfunction)}
    for name in members:
        assert not any(token in name.lower() for token in forbidden), (
            f"projection exposed a potential write-back surface: {name}"
        )


def test_render_functions_do_not_call_backend_mutators() -> None:
    # The render path reads ONLY `all_live`; it must not reference any mutating
    # backend method (write/invalidate/supersede). Source-level structural check.
    source = inspect.getsource(view)
    for mutator in (".write(", ".invalidate(", ".supersede("):
        assert mutator not in source, f"projection must not call backend mutator {mutator}"
