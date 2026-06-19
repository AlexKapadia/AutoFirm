"""Cross-provider write->read fidelity (T1) for the shared-knowledge plane (W2/B2).

Proves the core W2 interop guarantee with teeth (CLAUDE.md §3.6): a fact written by
a model on provider-A is retrieved AND acted on correctly by a model on provider-B,
through the SAME model-agnostic shared-context block -- no network, fakes only
(§5.5). The "act" step is a deterministic stand-in policy that reads the assembled
block; it succeeds iff the fact survived the cross-provider hop intact (value +
trusted taint), failing the action when a poisoned fact would have been needed.
"""

from __future__ import annotations

from autofirm.knowledge.cross_model_context_assembler import (
    AssembledContext,
    CrossModelContextAssembler,
)
from autofirm.knowledge.shared_knowledge_contract import TaintOrigin
from autofirm.memory.semantic_embedding_backend import DeterministicHashingEmbedder
from tests.knowledge.synthetic_knowledge_fixtures import (
    at_day,
    make_entry,
    make_graph,
    make_provenance,
)


def _provider_b_acts(block: AssembledContext, needle: str) -> str | None:
    """A deterministic provider-B 'policy': act ONLY on a TRUSTED fact matching needle.

    Mirrors propose-then-dispose: the consumer may use a value as a plan input only
    when it is trusted and the consequential gate is open. Returns the acted-upon
    value, or None when the policy (fail-closed) refuses.
    """
    if not block.consequential_action_allowed:
        return None  # gated: an untrusted value is present -> refuse to act
    for item in block.trusted_context:
        if needle in item.value:
            return item.value
    return None


def test_provider_a_write_is_read_and_acted_on_by_provider_b() -> None:
    # Provider-A (writer) commits a trusted fact; provider-B (reader, different
    # provider) assembles the model-agnostic block and acts correctly on it.
    g = make_graph()
    g.write(
        make_entry(
            entry_id="k1",
            subject="pricing_model",
            label="pricing_model",
            value="enterprise tier is 5000 per seat per year",
            origin=TaintOrigin.TRUSTED,
            provenance=make_provenance(written_by="agent-a", source_provider="provider-a"),
        )
    )
    # Provider-B reads via an independent embedder instance (heterogeneous consumer).
    assembler = CrossModelContextAssembler(embedder=DeterministicHashingEmbedder())
    block = assembler.assemble(
        backend=g,
        subject="pricing_model",
        query="enterprise tier seat price per year",
        as_of=at_day(2),
        limit=5,
    )
    acted = _provider_b_acts(block, needle="5000 per seat")
    assert acted == "enterprise tier is 5000 per seat per year"  # fidelity: intact


def test_cross_provider_action_refuses_when_only_an_untrusted_fact_exists() -> None:
    # If the only relevant fact is untrusted (e.g. scraped by another provider),
    # provider-B's policy fails closed -- the fact is delivered but NOT acted on.
    g = make_graph()
    g.write(
        make_entry(
            entry_id="k1",
            value="enterprise tier is 5000 per seat per year",
            origin=TaintOrigin.UNTRUSTED,
            provenance=make_provenance(written_by="scraper", source_provider="provider-c"),
        )
    )
    assembler = CrossModelContextAssembler(embedder=DeterministicHashingEmbedder())
    block = assembler.assemble(
        backend=g, subject="pricing_model", query="enterprise tier seat price", as_of=at_day(2),
        limit=5,
    )
    assert _provider_b_acts(block, needle="5000 per seat") is None  # fail-closed
    # The value is still visible to B as untrusted reference data (not lost).
    assert any("5000 per seat" in i.value for i in block.untrusted_context)


def test_as_of_time_governs_what_provider_b_sees() -> None:
    # Provider-A supersedes the fact on day 6; provider-B querying as-of day 3 acts
    # on the OLD value, as-of day 7 acts on the NEW value -- temporal fidelity holds
    # across the provider hop.
    g = make_graph()
    g.write(
        make_entry(entry_id="k1", value="price is 100 dollars", recorded_at=at_day(1),
                   origin=TaintOrigin.TRUSTED)
    )
    g.supersede(
        entry_id="k1",
        replacement=make_entry(entry_id="k2", value="price is 200 dollars",
                               recorded_at=at_day(6), origin=TaintOrigin.TRUSTED),
        superseded_at=at_day(6),
    )
    assembler = CrossModelContextAssembler(embedder=DeterministicHashingEmbedder())
    early = assembler.assemble(backend=g, subject="pricing_model", query="price dollars",
                               as_of=at_day(3), limit=5)
    late = assembler.assemble(backend=g, subject="pricing_model", query="price dollars",
                              as_of=at_day(7), limit=5)
    assert _provider_b_acts(early, needle="100 dollars") == "price is 100 dollars"
    assert _provider_b_acts(late, needle="200 dollars") == "price is 200 dollars"
    # The stale value never leaks into the late (current) view.
    assert all("100 dollars" not in i.value for i in late.all_items())
