"""The append-only, RFC-6962 hash-chained, tamper-evident cost ledger.

What this does
--------------
Defines :class:`AppendOnlyCostLedger` — an immutable, append-only sequence of
:class:`~autofirm.costledger.usage_cost_record.UsageCostRecord` rows chained with
the shared RFC-6962 ``leaf_hash``. Every append re-verifies the chain (fail-closed):
the new row's ``prev_hash`` must equal the current tip's ``record_hash``, and the
whole chain must re-verify. There is no update or delete path — a wrong row is
SUPERSEDED by a reversing entry (the exact-negative cost), never edited (§8).

Why it exists / where it sits
-----------------------------
``data-contracts.md`` §8 / ``SYNTHESIS.md`` §4: the cost ledger is append-only and
tamper-evident so any total is independently re-derivable and any reconciliation
discrepancy traces to a usage-parse bug or a stale price, never to an edited row.
This is mutation-critical (item 4). It mirrors
:class:`autofirm.capabilities.capability_growth_log.CapabilityGrowthLog` exactly —
the chaining discipline is written once and applied consistently. It sits above the
record contract and the canonical hashing helper; rollups and reconciliation read it.

Security / compliance invariants upheld
---------------------------------------
* **Append-only (§3.8 / §5.6):** :meth:`append` returns a NEW ledger; no update/
  delete. An out-of-order, duplicate, or chain-broken row is refused.
* **Tamper-evident (RFC-6962, fail-closed):** :meth:`verify` re-walks the whole
  chain and refuses on the first broken link — a reorder/insert/delete/edit anywhere
  is detected.
* **Verification-before-trust:** a ledger cannot be constructed around an
  unverifiable tuple — a corrupted chain fails closed at construction, never served.
* **Corrections are reversing entries (§8):** :meth:`seal_reversal` produces the
  exact-negative of a prior row so the chain is preserved and the audit trail keeps
  both the wrong row and its reversal.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from autofirm.audit.rfc6962_hashing import HASH_BYTES
from autofirm.costledger.cost_record_canonical_hashing import compute_cost_record_hash
from autofirm.costledger.usage_cost_record import (
    CostSource,
    PriceVector,
    TokenUsage,
    UsageCostRecord,
)
from autofirm.foundation.money.money_amount import Money
from autofirm.modelgateway.model_reference import ModelRef, UseCaseId
from autofirm.org.org_identifiers import RoleId

__all__ = ["GENESIS_PREV_HASH", "AppendOnlyCostLedger", "CostLedgerError"]

# The chain anchor for the FIRST row: an all-zero 32-byte hash. A genuine previous
# record_hash is a SHA-256 digest and is never all-zero, so the genesis link is
# unambiguous and cannot be confused with a real predecessor.
GENESIS_PREV_HASH = b"\x00" * HASH_BYTES


class CostLedgerError(Exception):
    """Raised when an append or verification would violate a ledger invariant."""


class AppendOnlyCostLedger:
    """An immutable, append-only, RFC-6962 hash-chained cost ledger.

    Built empty and grown via :meth:`seal` + :meth:`append`. Every mutator returns a
    NEW ledger; the underlying tuple is never edited in place, so any sequence of
    appends is a pure, replayable, tamper-evident fold.
    """

    __slots__ = ("_records",)

    def __init__(
        self, records: tuple[UsageCostRecord, ...] = (), *, _trusted: bool = False
    ) -> None:
        """Wrap ``records`` and fully verify the chain (fail-closed at construction).

        A ledger can only be observed if its chain verifies end to end, so a tampered
        tuple can never be wrapped and trusted. ``_trusted`` is a PRIVATE fast-path
        used ONLY by :meth:`append` — where the prefix was already verified at its own
        construction and the single new link is checked by :meth:`append` itself — so
        appending stays O(1) instead of re-verifying the whole chain O(n) every time
        (which would make building an n-row ledger O(n²)). It is never part of the
        public API; an externally-supplied tuple is ALWAYS fully verified.
        """
        self._records = records
        if not _trusted and not self._chain_is_intact():
            # fail-closed: never hold or serve an unverifiable chain.
            raise CostLedgerError("cost ledger chain failed verification (tamper detected)")

    @property
    def tip_hash(self) -> bytes:
        """The ``record_hash`` of the last row, or the genesis anchor if empty.

        This is the ``prev_hash`` the next sealed row must chain over, so a caller
        never reaches into the row list to extend the chain correctly.
        """
        return self._records[-1].record_hash if self._records else GENESIS_PREV_HASH

    def records(self) -> tuple[UsageCostRecord, ...]:
        """The ordered tuple of cost rows (the full recorded spend history)."""
        return self._records

    def append(self, record: UsageCostRecord) -> AppendOnlyCostLedger:
        """Return a NEW ledger with ``record`` appended (append-only, fail-closed).

        Refuses (does not append) if the row's ``prev_hash`` does not match the
        current tip (a reorder, insert, or forged predecessor) — so the ledger can
        never be rewritten, reordered, or have a row spliced in (§5.6). The row's
        own ``record_hash`` was already validated against its content at construction.
        """
        if record.prev_hash != self.tip_hash:
            # fail-closed: a prev_hash that does not chain the tip breaks the chain.
            raise CostLedgerError("record prev_hash does not match the ledger tip (broken chain)")
        # The prefix was verified when THIS ledger was built and the new link is
        # checked just above, so the result is provably intact — skip the O(n)
        # re-walk (keeps n appends O(n), not O(n²)). The record's own record_hash was
        # already validated against its content at its construction.
        return AppendOnlyCostLedger((*self._records, record), _trusted=True)

    def seal_new(  # noqa: PLR0913 -- a cost row is intrinsically wide; every field
        # is a distinct, required, keyword-only business input (no grab-bag dict).
        self,
        *,
        correlation_id: UUID,
        requesting_role_id: RoleId,
        use_case: UseCaseId,
        served_by: ModelRef,
        usage: TokenUsage,
        unit_prices: PriceVector,
        cost: Money,
        cost_source: CostSource,
        price_catalog_version: str,
        recorded_at: datetime,
    ) -> UsageCostRecord:
        """Build the next chained row from business fields (the ergonomic seal path).

        This is the single place a NEW row is created: it stamps ``prev_hash`` to the
        current tip, computes the ``record_hash`` over the canonical content, and
        returns a fully-valid :class:`UsageCostRecord` — so callers never compute a
        hash or guess a ``prev_hash`` themselves (§5.7). The returned row is then
        passed to :meth:`append`.
        """
        prev_hash = self.tip_hash
        # model_construct skips validation so we can compute the hash on the content
        # BEFORE the final validated construction (which requires the hash to match).
        draft = UsageCostRecord.model_construct(
            correlation_id=correlation_id,
            requesting_role_id=requesting_role_id,
            use_case=use_case,
            served_by=served_by,
            usage=usage,
            unit_prices=unit_prices,
            cost=cost,
            cost_source=cost_source,
            price_catalog_version=price_catalog_version,
            recorded_at=recorded_at,
            prev_hash=prev_hash,
            record_hash=GENESIS_PREV_HASH,
        )
        record_hash = compute_cost_record_hash(draft, prev_hash=prev_hash)
        return UsageCostRecord(
            correlation_id=correlation_id,
            requesting_role_id=requesting_role_id,
            use_case=use_case,
            served_by=served_by,
            usage=usage,
            unit_prices=unit_prices,
            cost=cost,
            cost_source=cost_source,
            price_catalog_version=price_catalog_version,
            recorded_at=recorded_at,
            prev_hash=prev_hash,
            record_hash=record_hash,
        )

    def seal(self, *, content: UsageCostRecord) -> UsageCostRecord:
        """Re-seal ``content`` so it chains over THIS ledger's tip (single hash writer).

        ``content`` carries every business field (usage, prices, cost, provenance,
        ids, timestamp); this stamps the correct ``prev_hash`` (the current tip) and
        recomputes the ``record_hash`` — so callers never compute or pass hashes
        themselves and a row always chains the real tip (§5.7).
        """
        return self._reseal(content, self.tip_hash)

    def seal_reversal(self, *, original: UsageCostRecord) -> UsageCostRecord:
        """Seal the exact-negative reversing entry for ``original`` (a correction, §8).

        Produces a new row identical to ``original`` except the ``cost`` is negated
        (exact ``Decimal``), chained over the current tip. Corrections are reversing
        entries, NEVER edits — both the wrong row and its reversal stay in the chain,
        so the audit trail and the chain integrity are preserved.
        """
        reversed_cost = Money(-original.cost.amount, original.cost.currency)
        reversal = original.model_copy(
            update={
                "cost": reversed_cost,
                "prev_hash": self.tip_hash,
                "record_hash": GENESIS_PREV_HASH,  # placeholder; _reseal recomputes it
            }
        )
        return self._reseal(reversal, self.tip_hash)

    def verify(self) -> bool:
        """Re-walk the whole chain; True iff every link and ``record_hash`` is intact.

        Independent of construction so a caller can re-verify a ledger it was handed
        (verification-before-trust). Checks each row's ``prev_hash`` chains the
        predecessor (genesis for the first) and its ``record_hash`` re-derives from
        its canonical content.
        """
        return self._chain_is_intact()

    def total(self, currency: str) -> Money:
        """Sum every row's cost in ``currency`` EXACTLY (fail-closed on a mismatch).

        Reversing entries (negative costs) net out naturally, so the total reflects
        corrections. Refuses if any row is denominated in a different currency — a
        cross-currency sum is meaningless (folder 09); convert via FX first.
        """
        running = Money(Decimal(0), currency)
        for record in self._records:
            # Money.__add__ is fail-closed on a currency mismatch (folder 09).
            running = running + record.cost
        return running

    def _reseal(self, content: UsageCostRecord, prev_hash: bytes) -> UsageCostRecord:
        """Recompute ``record_hash`` for ``content`` chained over ``prev_hash``."""
        record_hash = compute_cost_record_hash(content, prev_hash=prev_hash)
        return content.model_copy(update={"prev_hash": prev_hash, "record_hash": record_hash})

    def _chain_is_intact(self) -> bool:
        """Re-derive and compare every link; False on the first broken/edited row."""
        expected_prev = GENESIS_PREV_HASH
        for record in self._records:
            if record.prev_hash != expected_prev:
                return False  # a broken/forged/reordered chain link
            recomputed = compute_cost_record_hash(record, prev_hash=record.prev_hash)
            if recomputed != record.record_hash:
                return False  # the stored hash does not match the content (edited)
            expected_prev = record.record_hash
        return True
