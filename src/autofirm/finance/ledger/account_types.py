"""Typed chart-of-accounts primitives for the double-entry ledger.

What this does
--------------
Defines the five fundamental account classes of double-entry bookkeeping
(Asset, Liability, Equity, Revenue, Expense) and the *normal balance side* of
each. The normal side determines how a debit or a credit moves an account's
balance, which is the rule the ledger uses to roll journal postings up into the
three financial statements.

Why it exists / where it sits
-----------------------------
This is the vocabulary every other finance module is written against. The
account class drives statement classification (Asset/Liability/Equity ->
balance sheet; Revenue/Expense -> income statement) and the sign convention that
makes ``Assets = Liabilities + Equity`` hold by construction (CLAUDE.md §3.11
zero-numerical-error). Keeping it in one tiny, single-responsibility module
means the convention is declared exactly once and reused everywhere.

Security / compliance invariants upheld
---------------------------------------
The account class is a closed ``Enum`` — an unknown account type cannot be
constructed, so a malformed account is refused at the type boundary rather than
silently misclassified (fail-closed, CLAUDE.md §5.6).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = ["Account", "AccountType", "NormalSide"]


class NormalSide(Enum):
    """The side on which an account class normally carries a positive balance.

    Debit-normal accounts (assets, expenses) increase with debits; credit-normal
    accounts (liabilities, equity, revenue) increase with credits. This is the
    sign rule that ties the trial balance to zero and keeps the accounting
    identity exact.
    """

    DEBIT = "debit"
    CREDIT = "credit"


class AccountType(Enum):
    """The five fundamental account classes of double-entry accounting.

    Closed set: a value outside these five cannot exist, so an account can never
    be silently misclassified onto the wrong statement (fail-closed).
    """

    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"

    @property
    def normal_side(self) -> NormalSide:
        """Return the normal balance side for this account class.

        Assets and expenses are debit-normal; liabilities, equity and revenue
        are credit-normal. This mapping is the single source of truth for how a
        posting changes an account balance (used by the ledger and statements).
        """
        # WHY: debit-normal == the "left side" classes (what you own / what you
        # spend); everything else is credit-normal. Encoding it here once stops
        # every caller from re-deriving (and risking) the sign convention.
        if self in (AccountType.ASSET, AccountType.EXPENSE):
            return NormalSide.DEBIT
        return NormalSide.CREDIT


@dataclass(frozen=True, slots=True)
class Account:
    """An immutable account in the chart of accounts.

    Args:
        code: A stable, unique identifier for the account (e.g. ``"1000"`` for
            Cash). Used as the ledger key; must be non-empty.
        name: A human-readable account name (e.g. ``"Cash"``).
        type: The account class, which fixes its statement and normal side.

    Raises:
        ValueError: If ``code`` or ``name`` is empty/blank (fail-closed: an
            unidentifiable account is refused — CLAUDE.md §5.6).
    """

    code: str
    name: str
    type: AccountType

    def __post_init__(self) -> None:
        """Reject blank identifiers so no posting can target a nameless account."""
        if not self.code or not self.code.strip():  # fail-closed: account must be identifiable
            raise ValueError("account code must be a non-empty string")
        if not self.name or not self.name.strip():  # fail-closed: account must be named
            raise ValueError("account name must be a non-empty string")

    @property
    def normal_side(self) -> NormalSide:
        """The normal balance side, delegated to the account class."""
        return self.type.normal_side
