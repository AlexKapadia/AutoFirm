"""Cash-flow statement — operating/investing/financing, ties to the cash delta.

What this does
--------------
Derives the cash-flow statement directly from the ledger by walking every
journal entry that moves a *cash* account and classifying that movement into one
of IAS 7's three activities — **operating, investing, financing** — by the type
of the counterpart (non-cash) accounts in the same entry. The defining invariant
is enforced fail-closed: **operating + investing + financing == the change in
the cash balance**, to the cent.

Classification rule (IAS 7, research source 03)
-----------------------------------------------
For a cash entry, the non-cash legs decide the activity:

* counterpart is **Revenue or Expense** -> *operating* (principal
  revenue-producing activities).
* counterpart is a **non-cash Asset** (e.g. equipment, investments) ->
  *investing* (acquisition/disposal of long-term assets).
* counterpart is a **Liability or Equity** -> *financing* (changes in borrowings
  and contributed equity).

Why it exists / where it sits
-----------------------------
Statement three of the articulation. Building it from the same immutable ledger
and tying its total to the balance-sheet cash delta is the cross-statement
correctness check (SYNTHESIS §1; CLAUDE.md §3.11). A statement whose total does
not tie is *refused* (fail-closed, §5.6).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from autofirm.finance.ledger.account_types import Account, AccountType
from autofirm.finance.ledger.double_entry_ledger import DoubleEntryLedger, _signed_delta
from autofirm.finance.ledger.journal_entry import JournalEntry, Posting

__all__ = ["CashFlowStatement"]


def _is_cash(account: Account, cash_codes: frozenset[str]) -> bool:
    """True if ``account`` is one of the designated cash accounts."""
    return account.code in cash_codes


def _activity_of(counterpart_type: AccountType) -> str:
    """Map a counterpart account type to its IAS 7 activity bucket.

    Args:
        counterpart_type: The non-cash leg's account type.

    Returns:
        ``"operating"``, ``"investing"`` or ``"financing"`` per IAS 7 (source 03).
    """
    if counterpart_type in (AccountType.REVENUE, AccountType.EXPENSE):
        return "operating"  # principal revenue-producing activities (IAS 7)
    if counterpart_type is AccountType.ASSET:
        return "investing"  # acquisition/disposal of (non-cash) long-term assets
    return "financing"  # liabilities + equity: borrowings and contributed capital


@dataclass(frozen=True, slots=True)
class CashFlowStatement:
    """A cash-flow statement whose net change ties to the balance-sheet cash delta.

    Attributes:
        operating: Net cash from operating activities (exact Decimal).
        investing: Net cash from investing activities (exact Decimal).
        financing: Net cash from financing activities (exact Decimal).
    """

    operating: Decimal
    investing: Decimal
    financing: Decimal

    @classmethod
    def from_ledger(
        cls, ledger: DoubleEntryLedger, cash_codes: frozenset[str]
    ) -> CashFlowStatement:
        """Build the cash-flow statement and tie its net to the cash delta.

        Each entry that moves a cash account contributes its signed cash delta to
        the activity implied by the entry's non-cash legs. The three buckets are
        summed exactly, then re-checked against the cash balance change.

        Args:
            ledger: The double-entry ledger to read.
            cash_codes: Account codes treated as cash / cash-equivalents.

        Returns:
            A :class:`CashFlowStatement` whose ``net_change`` equals the cash delta.

        Raises:
            ValueError: If ``cash_codes`` is empty, or the classified net change
                does not equal the ledger cash delta to the cent (fail-closed —
                CLAUDE.md §5.6).
        """
        if not cash_codes:  # fail-closed: a cash-flow statement needs a cash account
            raise ValueError("cash_codes must designate at least one cash account")

        buckets = {"operating": Decimal("0.00"), "investing": Decimal("0.00"),
                   "financing": Decimal("0.00")}
        for entry in ledger.entries():
            cash_delta = _entry_cash_delta(entry, cash_codes)
            if cash_delta == Decimal("0.00"):
                continue  # no cash moved -> not a cash-flow event
            activity = _classify_entry(entry, cash_codes)
            buckets[activity] += cash_delta

        statement = cls(
            operating=buckets["operating"],
            investing=buckets["investing"],
            financing=buckets["financing"],
        )
        # fail-closed: the net of the three activities MUST equal the actual
        # change in the cash balance to the cent (the cross-statement tie).
        actual_cash_delta = _ledger_cash_delta(ledger, cash_codes)
        if statement.net_change() != actual_cash_delta:
            raise ValueError(
                "cash-flow statement does not tie: net "
                f"{statement.net_change()} != cash delta {actual_cash_delta}"
            )
        return statement

    def net_change(self) -> Decimal:
        """Net change in cash == operating + investing + financing (exact)."""
        return self.operating + self.investing + self.financing


def _entry_cash_delta(entry: JournalEntry, cash_codes: frozenset[str]) -> Decimal:
    """Exact signed change to cash produced by one journal entry."""
    delta = Decimal("0.00")
    for posting in entry.postings:
        if _is_cash(posting.account, cash_codes):
            # Cash is an asset (debit-normal); a debit increases cash, a credit
            # decreases it. _signed_delta encodes exactly that sign convention.
            delta += _signed_delta(
                posting.side, posting.account.normal_side, posting.amount
            )
    return delta


def _classify_entry(entry: JournalEntry, cash_codes: frozenset[str]) -> str:
    """Classify a cash entry by its non-cash legs (IAS 7 activity).

    The non-cash postings decide the activity. We use the largest non-cash leg by
    magnitude (ties -> first in entry order) so the rule is deterministic even
    when an entry mixes counterpart types.
    """
    non_cash: list[Posting] = [p for p in entry.postings if not _is_cash(p.account, cash_codes)]
    # WHY: pick the dominant counterpart deterministically — sort by descending
    # magnitude, stable on entry order, so identical entries always classify the
    # same way (determinism, CLAUDE.md §3.6).
    dominant = max(non_cash, key=lambda p: p.amount)
    return _activity_of(dominant.account.type)


def _ledger_cash_delta(ledger: DoubleEntryLedger, cash_codes: frozenset[str]) -> Decimal:
    """Total change in the cash balance across all cash accounts (exact)."""
    delta = Decimal("0.00")
    for account in ledger.accounts():
        if account.code in cash_codes:
            delta += ledger.balance_of(account)  # cash is debit-normal: balance == net inflow
    return delta
