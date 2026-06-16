"""Balanced journal entries — the atomic, fail-closed unit of the ledger.

What this does
--------------
Defines :class:`Posting` (one debit or credit to one account, in exact money)
and :class:`JournalEntry` (a set of postings that must balance). The defining
invariant of double-entry bookkeeping — **total debits == total credits** — is
enforced at construction: an unbalanced entry is *refused*, never recorded.

Why it exists / where it sits
-----------------------------
Every change to the ledger goes through a :class:`JournalEntry`. Because each
entry is provably balanced before it is accepted, the trial balance is always
zero and the downstream identity ``Assets = Liabilities + Equity`` holds by
construction (CLAUDE.md §3.11 zero-numerical-error). All amounts are exact
:class:`~decimal.Decimal` minor-unit values — IEEE-754 floats are never used for
money (foundation ``exact_money_arithmetic`` contract).

Security / compliance invariants upheld
---------------------------------------
Fail-closed validation (CLAUDE.md §5.6): a non-positive posting amount, an empty
entry, a sub-minor-unit amount, or debits != credits each raise ``ValueError``
rather than being silently coerced. Entries are frozen (append-only / immutable)
so a recorded fact cannot be mutated after the fact (audit integrity).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from autofirm.finance.ledger.account_types import Account
from autofirm.foundation.money.exact_money_arithmetic import minor_units

__all__ = ["JournalEntry", "Posting", "PostingSide"]

# Double-entry needs at least one debit and one credit, hence two postings.
_MIN_POSTINGS_PER_ENTRY = 2


class PostingSide(Enum):
    """Which side of the ledger a single posting hits."""

    DEBIT = "debit"
    CREDIT = "credit"


@dataclass(frozen=True, slots=True)
class Posting:
    """A single debit or credit of an exact amount to one account.

    Args:
        account: The account being moved.
        side: ``DEBIT`` or ``CREDIT``.
        amount: A strictly-positive, cent-exact :class:`~decimal.Decimal`. The
            sign lives in ``side``, never in the amount, so a "negative debit"
            cannot masquerade as a credit.

    Raises:
        ValueError: If ``amount`` is not strictly positive, or is not exactly
            representable in minor units (fail-closed — CLAUDE.md §5.6).
    """

    account: Account
    side: PostingSide
    amount: Decimal

    def __post_init__(self) -> None:
        """Reject non-positive or sub-cent amounts so every posting is exact."""
        if self.amount <= Decimal(0):  # fail-closed: amount carries magnitude only
            raise ValueError(f"posting amount must be strictly positive, got {self.amount}")
        # Reuse the foundation validator: refuses anything finer than a cent.
        minor_units(self.amount)  # fail-closed: sub-minor-unit precision is refused


@dataclass(frozen=True, slots=True)
class JournalEntry:
    """A balanced set of postings recorded as one atomic transaction.

    The construction-time invariant ``sum(debits) == sum(credits)`` is the
    backbone of double-entry correctness. An entry that does not balance is
    rejected — it can never enter the ledger (fail-closed).

    Args:
        description: A short human-readable memo (audit trail). Must be non-empty.
        postings: Two or more :class:`Posting` objects that balance.

    Raises:
        ValueError: If there are fewer than two postings, the description is
            blank, or debits != credits (fail-closed — CLAUDE.md §5.6).
    """

    description: str
    postings: tuple[Posting, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Enforce the debits==credits invariant before the entry is accepted."""
        if not self.description or not self.description.strip():  # fail-closed: audit memo required
            raise ValueError("journal entry description must be non-empty")
        if len(self.postings) < _MIN_POSTINGS_PER_ENTRY:  # fail-closed: needs >=2 postings
            raise ValueError("a journal entry needs at least two postings")
        total_debit = self.total_debits()
        total_credit = self.total_credits()
        if total_debit != total_credit:  # fail-closed: THE double-entry invariant
            raise ValueError(
                f"journal entry does not balance: debits {total_debit} != credits {total_credit}"
            )

    def total_debits(self) -> Decimal:
        """Exact sum of every debit posting (Decimal, never float)."""
        # WHY: summing only DEBIT-side magnitudes; sign is encoded in side, so a
        # plain Decimal sum is exact and order-independent.
        return sum(
            (p.amount for p in self.postings if p.side is PostingSide.DEBIT),
            start=Decimal("0.00"),
        )

    def total_credits(self) -> Decimal:
        """Exact sum of every credit posting (Decimal, never float)."""
        return sum(
            (p.amount for p in self.postings if p.side is PostingSide.CREDIT),
            start=Decimal("0.00"),
        )
