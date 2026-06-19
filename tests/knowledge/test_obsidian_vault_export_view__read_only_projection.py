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
from tests.knowledge.synthetic_knowledge_fixtures import (
    at_day,
    make_entry,
    make_graph,
    make_provenance,
)


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


def test_render_entry_note_emits_the_exact_markdown_template_with_em_dash_fallbacks() -> None:
    # Pins the FULL note template byte-for-byte for a still-valid, non-derived entry.
    # Kills every template-literal mutant (each header label, the wikilink brackets,
    # the arrow separator) AND BOTH "—" fallbacks (invalid_at None -> "—"; empty
    # derived_from -> "—"). The prior substring-only checks let these survive.
    entry = make_entry(
        entry_id="k1",
        subject="pricing_model",
        label="pricing_model",
        description="the current pricing model",
        value="monthly subscription at fixed tiers",
        origin=TaintOrigin.TRUSTED,
        provenance=make_provenance(written_by="planner", source_provider="provider-x"),
        valid_at=at_day(1),
        invalid_at=None,  # exercises the "—" fallback on the event-validity line
    )
    note = view.render_entry_note(entry)
    expected = (
        "# pricing_model\n\n"
        "**Subject:** [[pricing_model]]\n\n"
        "**Origin (taint):** trusted\n\n"
        "**Written by:** planner (provider: provider-x)\n\n"
        f"**Valid:** {at_day(1).isoformat()} → —\n\n"  # invalid_at None -> em-dash
        "**Derived from:** —\n\n"  # empty derived_from -> em-dash
        "the current pricing model\n\n"
        "> monthly subscription at fixed tiers\n"
    )
    assert note == expected


def test_render_entry_note_emits_invalid_date_and_lineage_when_present() -> None:
    # The OTHER branch of each conditional on lines 54-55: a SET invalid_at renders
    # its ISO timestamp (not "—"), and a non-empty derived_from renders the
    # "[[src]]" wikilinks joined by ", " (not "—"). Kills mutants that swap the
    # populated branch for the fallback (and the join separator / wikilink brackets).
    entry = make_entry(
        entry_id="k2",
        subject="headcount",
        label="headcount",
        value="hire two backend engineers",
        origin=TaintOrigin.UNTRUSTED,
        provenance=make_provenance(
            written_by="scraper",
            source_provider="provider-y",
            derived_from=("src-a", "src-b"),
        ),
        valid_at=at_day(2),
        invalid_at=at_day(9),  # exercises the ISO-format branch (not the "—")
    )
    note = view.render_entry_note(entry)
    assert f"**Valid:** {at_day(2).isoformat()} → {at_day(9).isoformat()}\n\n" in note
    assert "**Derived from:** [[src-a]], [[src-b]]\n\n" in note  # joined wikilinks
    assert "**Origin (taint):** untrusted\n\n" in note  # untrusted taint surfaced
    assert "**Written by:** scraper (provider: provider-y)\n\n" in note


def test_render_vault_filename_is_exactly_the_entry_id_dot_md() -> None:
    # Pins the vault key format ("<entry_id>.md"); kills a mutant on the filename
    # f-string (dropping ".md" or the id) that the live/deterministic tests miss.
    g = make_graph()
    g.write(make_entry(entry_id="weird-id-7", value="some content"))
    vault = view.render_vault(g)
    assert set(vault) == {"weird-id-7.md"}
