"""Canonical serialisation + RFC-6962 leaf hashing for one ``UsageCostRecord``.

What this does
--------------
Provides :func:`canonical_cost_record_bytes` — the deterministic, injective byte
encoding of a cost-ledger row's *content* (every committed field except the output
``record_hash``, with ``prev_hash`` folded in) — and :func:`compute_cost_record_hash`,
which feeds that encoding to the shared RFC-6962 ``leaf_hash``. Together they are
the single definition of "what a ledger row hashes to", reused by the record's
construction-time tamper check and by the append-only ledger's chaining + verify.

Why it exists / where it sits
-----------------------------
Kept separate from :mod:`usage_cost_record` so each file has one responsibility and
stays well under the 300-line limit (§5.7), and so the record contract and the
append-only log share *one* canonicalisation (no drift between "what we hash on
construct" and "what we re-hash on verify"). Mirrors
:mod:`autofirm.capabilities.capability_registry_event`'s canonicalisation exactly
(sorted keys, tight separators, UTC-normalised timestamp, hex hashes), and reuses
:func:`autofirm.audit.rfc6962_hashing.leaf_hash` — the chaining primitive is never
re-implemented.

Security / compliance invariants upheld
---------------------------------------
* **Deterministic + injective (CLAUDE.md §3.11):** sorted keys, no whitespace,
  UTC-normalised timestamp, and the full ``Decimal`` string of every price/amount —
  so an identical row always yields identical bytes and two distinct rows never
  collide on the encoding.
* **prev_hash bound into the preimage (tamper-evidence):** the chain position is
  part of what the hash commits to, so editing any earlier row changes every later
  ``record_hash`` (the §8 tamper-evidence property).
* **record_hash is the OUTPUT, never the input:** it is deliberately excluded from
  the preimage, so the hash cannot be made to "agree with itself".
"""

from __future__ import annotations

import json
from datetime import UTC
from typing import TYPE_CHECKING

from autofirm.audit.rfc6962_hashing import leaf_hash

if TYPE_CHECKING:  # avoid a runtime import cycle (the record imports this module)
    from autofirm.costledger.usage_cost_record import UsageCostRecord

__all__ = [
    "canonical_cost_record_bytes",
    "compute_cost_record_hash",
]


def canonical_cost_record_bytes(record: UsageCostRecord, *, prev_hash: bytes) -> bytes:
    """Serialise a cost row's content to canonical, deterministic, injective bytes.

    Every committed field is encoded with sorted keys and tight separators; the
    timestamp is UTC-normalised; the cost amount and every price are encoded as
    their full ``Decimal`` string (never a float) so no precision is lost; and
    ``prev_hash`` is folded in as hex so the hash commits to the chain position.
    The ``record_hash`` is intentionally NOT part of the preimage (it is the OUTPUT).

    Args:
        record: The cost row whose content to encode (its own ``prev_hash`` /
            ``record_hash`` are ignored here in favour of the explicit ``prev_hash``).
        prev_hash: The chain link this row is being hashed over (the previous row's
            ``record_hash``, or the genesis anchor for the first row).

    Returns:
        The canonical UTF-8 byte serialisation of the row's content.
    """
    recorded = record.recorded_at
    recorded = recorded if recorded.tzinfo is not None else recorded.replace(tzinfo=UTC)
    recorded = recorded.astimezone(UTC)
    prices = record.unit_prices
    payload = {
        "correlation_id": str(record.correlation_id),
        "requesting_role_id": str(record.requesting_role_id),
        "use_case": str(record.use_case),
        "served_by": {
            "provider": prices_provider(record),
            "model_name": record.served_by.model_name,
        },
        "usage": {
            "input_tokens": record.usage.input_tokens,
            "output_tokens": record.usage.output_tokens,
            "cache_read_tokens": record.usage.cache_read_tokens,
            "cache_write_tokens": record.usage.cache_write_tokens,
            "reasoning_tokens": record.usage.reasoning_tokens,
        },
        "unit_prices": {
            "currency": prices.currency,
            # Full Decimal strings — encoding a float here would re-import drift.
            "input_price": str(prices.input_price),
            "output_price": str(prices.output_price),
            "cache_read_price": str(prices.cache_read_price),
            "cache_write_price": str(prices.cache_write_price),
            "reasoning_price": str(prices.reasoning_price),
            "tier_threshold_tokens": prices.tier_threshold_tokens,
            "input_price_above_threshold": _opt_decimal_str(prices.input_price_above_threshold),
            "output_price_above_threshold": _opt_decimal_str(prices.output_price_above_threshold),
        },
        "cost": {
            "amount": str(record.cost.amount),  # exact Decimal string, never float
            "currency": record.cost.currency,
        },
        "cost_source": record.cost_source,
        "price_catalog_version": record.price_catalog_version,
        "recorded_at": recorded.isoformat(),
        "prev_hash": prev_hash.hex(),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_cost_record_hash(record: UsageCostRecord, *, prev_hash: bytes) -> bytes:
    """Compute the RFC-6962 leaf hash chaining a row's content over ``prev_hash``.

    ``prev_hash`` is folded into the canonical preimage, so the hash commits to BOTH
    this row and its position in the chain — editing any earlier row changes every
    later ``record_hash`` (the tamper-evidence property).
    """
    return leaf_hash(canonical_cost_record_bytes(record, prev_hash=prev_hash))


def prices_provider(record: UsageCostRecord) -> str:
    """Return the provider identity as its stable string value (enum -> str).

    Encoding the enum's ``.value`` (not its ``repr``) keeps the canonical bytes
    stable across Python/enum representation changes (determinism, §3.11).
    """
    return record.served_by.provider.value


def _opt_decimal_str(value: object) -> str | None:
    """Encode an optional ``Decimal`` tier price as its exact string, or ``None``."""
    return None if value is None else str(value)
