"""The double-entry ledger — records balanced entries, computes balances.

What this does
--------------
:class:`DoubleEntryLedger` accepts :class:`~autofirm.finance.ledger.journal_entry.JournalEntry`
objects (each already proven to balance) and maintains the running balance of
every account in *signed normal-side* terms. It exposes:

* :meth:`balance_of` — one account's balance (positive == its normal side).
* :meth:`trial_balance` — the sum of all signed balances, which must be exactly
  zero (the global correctness check).

Why it exists / where it sits
-----------------------------
This is the single source of truth the three statements are derived from. Because
every entry balances and balances are computed with exact :class:`~decimal.Decimal`
arithmetic, the trial balance is exactly zero and the statements reconcile to the
cent (CLAUDE.md §3.11). Balances are recomputed from the immutable entry log, so
the ledger is an append-only fact store (audit integrity, CLAUDE.md §5.6).

Security / compliance invariants upheld
---------------------------------------
The entry log is append-only; :meth:`post` never mutates a recorded entry. The
signed-balance convention is applied uniformly, so no account can drift off its
normal side without it showing up as a non-zero trial balance (fail-closed
detectability).
"""

from __future__ import annotations

from decimal import Decimal

from autofirm.finance.ledger.account_types import Account, NormalSide
from autofirm.finance.ledger.journal_entry import JournalEntry, PostingSide

__all__ = ["DoubleEntryLedger"]


def _signed_delta(side: PostingSide, normal_side: NormalSide, amount: Decimal) -> Decimal:
    """Return the signed change to an account's normal-side balance.

    A posting on the account's normal side increases the balance; a posting on
    the opposite side decreases it. Encoding the rule here once keeps the sign
    convention exact and identical everywhere (CLAUDE.md §3.11).

    Args:
        side: The side this posting hits.
        normal_side: The account's normal balance side.
        amount: The strictly-positive posting magnitude.

    Returns:
        ``+amount`` if the posting is on the normal side, else ``-amount``.
    """
    posting_is_debit = side is PostingSide.DEBIT
    normal_is_debit = normal_side is NormalSide.DEBIT
    # WHY: same side as normal -> increase; opposite side -> decrease. The XOR of
    # the two booleans tells us whether the posting opposes the normal side.
    if posting_is_debit == normal_is_debit:
        return amount
    return -amount


class DoubleEntryLedger:
    """An append-only double-entry ledger over exact-money journal entries."""

    def __init__(self) -> None:
        """Start an empty ledger with no entries and no balances."""
        self._entries: list[JournalEntry] = []
        # Signed normal-side balance per account code (Decimal, never float).
        self._balances: dict[str, Decimal] = {}
        # Keep the Account object per code so statements can read its type/name.
        self._accounts: dict[str, Account] = {}

    def post(self, entry: JournalEntry) -> None:
        """Record a balanced entry and update each touched account's balance.

        The entry is already proven balanced at construction, so posting can
        never unbalance the ledger. Balances accumulate in exact Decimal.

        Args:
            entry: A balanced :class:`JournalEntry`.
        """
        self._entries.append(entry)  # append-only: recorded facts are immutable
        for posting in entry.postings:
            account = posting.account
            self._accounts[account.code] = account
            delta = _signed_delta(posting.side, account.normal_side, posting.amount)
            current = self._balances.get(account.code, Decimal("0.00"))
            self._balances[account.code] = current + delta

    def balance_of(self, account: Account) -> Decimal:
        """Return the signed normal-side balance of one account (0 if untouched)."""
        return self._balances.get(account.code, Decimal("0.00"))

    def accounts(self) -> tuple[Account, ...]:
        """Return every account that has been posted to, in first-seen order."""
        return tuple(self._accounts.values())

    def trial_balance(self) -> Decimal:
        """Sum of every signed account balance — must be exactly zero.

        Because debit-normal balances are stored ``+`` on debits and credit-
        normal ``+`` on credits, a correct ledger sums to a non-zero number only
        if debits != credits somewhere. We therefore re-derive the signed sum in
        raw debit/credit terms: debit-normal balances count ``+``, credit-normal
        count ``-`` — a balanced ledger nets to exactly ``Decimal("0.00")``.
        """
        total = Decimal("0.00")
        for code, balance in self._balances.items():
            account = self._accounts[code]
            # Convert normal-side balance back to raw debit-positive terms so the
            # global debits-minus-credits sum is exactly zero on a balanced ledger.
            if account.normal_side is NormalSide.DEBIT:
                total += balance
            else:
                total -= balance
        return total

    def entries(self) -> tuple[JournalEntry, ...]:
        """Return the immutable, append-only entry log in posting order."""
        return tuple(self._entries)
