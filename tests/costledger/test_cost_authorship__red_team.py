"""Red-team tests: an agent cannot forge a cost number or self-declare attribution.

Trust-boundary abuse cases (CLAUDE.md §3.6 red-team, threat-model C9). The cost is a
PURE function of (attested usage, versioned price snapshot) — an agent cannot inject an
arbitrary cost and have it survive recomputation, cannot make a tampered row chain into
the ledger, and the attribution (requesting_role_id) is recorded verbatim from the
caller, never a value the cost engine itself invents.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from autofirm.costledger.append_only_cost_ledger import (
    GENESIS_PREV_HASH,
    AppendOnlyCostLedger,
)
from autofirm.costledger.cost_record_canonical_hashing import compute_cost_record_hash
from autofirm.costledger.exact_cost_computation import compute_exact_cost
from autofirm.costledger.usage_cost_record import UsageCostRecord
from autofirm.foundation.money.money_amount import Money
from tests.costledger.synthetic_cost_fixtures import (
    FIXED_INSTANT,
    corr,
    make_model,
    make_prices,
    make_usage,
    money,
    role,
    use_case,
)


def test_cost_is_a_pure_function_recompute_matches() -> None:
    # The ONLY legitimate cost is f(usage, prices). Anyone can recompute it from the
    # row's own attested usage + frozen prices and must get the SAME number.
    usage = make_usage(input_tokens=1_234_567, output_tokens=89_012)
    prices = make_prices()
    legitimate = compute_exact_cost(usage, prices)
    # Independent recomputation from the same attested inputs == the cost.
    assert compute_exact_cost(usage, prices) == legitimate


def test_agent_cannot_inject_arbitrary_cost_into_a_record() -> None:
    # An agent tries to claim a cost of 0.00 for a call that really cost 3.00, but
    # leaves the real usage/prices on the row. The record_hash is computed over the
    # content; a row whose hash is honestly computed STILL stores the forged cost —
    # so the DEFENCE is recomputation at audit/reconciliation time, which diverges.
    usage = make_usage(input_tokens=1_000_000, output_tokens=0)  # truly 3.00
    prices = make_prices()
    forged_cost = money("0.00")  # the lie
    ledger = AppendOnlyCostLedger()
    # The ledger seals from the business fields; an attacker passing a forged cost
    # produces a row that does NOT match the recomputation of f(usage, prices).
    rec = ledger.seal_new(
        correlation_id=corr(1), requesting_role_id=role("r"), use_case=use_case("uc"),
        served_by=make_model(), usage=usage, unit_prices=prices, cost=forged_cost,
        cost_source="price_map_computed", price_catalog_version="1.0.0",
        recorded_at=FIXED_INSTANT,
    )
    recomputed = compute_exact_cost(rec.usage, rec.unit_prices)
    assert rec.cost != recomputed  # the forgery is DETECTABLE by recomputation
    assert recomputed == Money(Decimal("3.00"), "USD")


def test_tampered_cost_row_cannot_chain_into_ledger() -> None:
    # An attacker edits a committed row's cost AFTER sealing, keeping the old hash.
    # Construction of the edited row fails (hash mismatch) — it can never be appended.
    ledger = AppendOnlyCostLedger()
    rec = ledger.seal_new(
        correlation_id=corr(1), requesting_role_id=role("r"), use_case=use_case("uc"),
        served_by=make_model(), usage=make_usage(input_tokens=1_000_000, output_tokens=0),
        unit_prices=make_prices(), cost=money("3.00"),
        cost_source="price_map_computed", price_catalog_version="1.0.0",
        recorded_at=FIXED_INSTANT,
    )
    # Re-validating an edited copy (stale hash, new cost) is refused fail-closed.
    edited = rec.model_copy(update={"cost": money("0.00")})
    with pytest.raises(ValidationError, match="tamper-evident"):
        UsageCostRecord.model_validate(dict(edited))


def test_requesting_role_id_is_recorded_verbatim_not_invented() -> None:
    # The cost engine never invents attribution: the role on the row is exactly the
    # one supplied by the (authenticated) caller. compute_exact_cost takes NO role at
    # all — cost cannot depend on who claims it.
    import inspect

    sig = inspect.signature(compute_exact_cost)
    assert "requesting_role_id" not in sig.parameters
    assert "role" not in sig.parameters
    # And the row carries the caller-supplied id unchanged.
    ledger = AppendOnlyCostLedger()
    rec = ledger.seal_new(
        correlation_id=corr(1), requesting_role_id=role("authenticated-role-7"),
        use_case=use_case("uc"), served_by=make_model(), usage=make_usage(),
        unit_prices=make_prices(), cost=compute_exact_cost(make_usage(), make_prices()),
        cost_source="price_map_computed", price_catalog_version="1.0.0",
        recorded_at=FIXED_INSTANT,
    )
    assert rec.requesting_role_id == "authenticated-role-7"


def test_cost_does_not_depend_on_provenance_label() -> None:
    # Switching the cost_source label must NOT change the computed cost — provenance
    # is a label, not an input to the arithmetic.
    usage, prices = make_usage(input_tokens=1_000_000, output_tokens=0), make_prices()
    cost = compute_exact_cost(usage, prices)
    ledger = AppendOnlyCostLedger()
    for src in ("price_map_computed", "provider_reported"):
        rec = ledger.seal_new(
            correlation_id=corr(1), requesting_role_id=role("r"), use_case=use_case("uc"),
            served_by=make_model(), usage=usage, unit_prices=prices, cost=cost,
            cost_source=src, price_catalog_version="1.0.0", recorded_at=FIXED_INSTANT,
        )
        assert rec.cost == Money(Decimal("3.00"), "USD")


def test_genesis_anchor_is_not_a_real_record_hash() -> None:
    # A forged "previous" row cannot masquerade as genesis: the genesis anchor is all
    # zeros, which a real SHA-256 record_hash is never equal to.
    ledger = AppendOnlyCostLedger()
    rec = ledger.seal_new(
        correlation_id=corr(1), requesting_role_id=role("r"), use_case=use_case("uc"),
        served_by=make_model(), usage=make_usage(), unit_prices=make_prices(),
        cost=compute_exact_cost(make_usage(), make_prices()),
        cost_source="price_map_computed", price_catalog_version="1.0.0",
        recorded_at=FIXED_INSTANT,
    )
    assert rec.record_hash != GENESIS_PREV_HASH
    assert compute_cost_record_hash(rec, prev_hash=GENESIS_PREV_HASH) == rec.record_hash
