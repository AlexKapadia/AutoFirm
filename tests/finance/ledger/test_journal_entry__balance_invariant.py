"""Adversarial + property tests for the debits==credits journal-entry invariant.

This is the load-bearing fail-closed control of the ledger (CLAUDE.md §5.6): an
unbalanced entry must be REFUSED. The property test proves the invariant over
arbitrary valid posting sets; the boundary tests pin the exact failure modes
(off-by-a-cent, non-positive amounts, sub-cent precision, too-few postings).
Designed to KILL mutants on ``journal_entry`` and ``account_types``.
"""

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from autofirm.finance.ledger.account_types import Account, AccountType, NormalSide
from autofirm.finance.ledger.journal_entry import JournalEntry, Posting, PostingSide

CASH = Account("1000", "Cash", AccountType.ASSET)
EQUITY = Account("3000", "Common Stock", AccountType.EQUITY)
LOAN = Account("2000", "Bank Loan", AccountType.LIABILITY)


def _deb(account: Account, amount: str) -> Posting:
    return Posting(account, PostingSide.DEBIT, Decimal(amount))


def _cre(account: Account, amount: str) -> Posting:
    return Posting(account, PostingSide.CREDIT, Decimal(amount))


# --------------------------------------------------------------------------- #
# Account-type normal-side convention (boundary-exact).                        #
# --------------------------------------------------------------------------- #


def test_asset_and_expense_are_debit_normal() -> None:
    assert AccountType.ASSET.normal_side is NormalSide.DEBIT
    assert AccountType.EXPENSE.normal_side is NormalSide.DEBIT


def test_liability_equity_revenue_are_credit_normal() -> None:
    assert AccountType.LIABILITY.normal_side is NormalSide.CREDIT
    assert AccountType.EQUITY.normal_side is NormalSide.CREDIT
    assert AccountType.REVENUE.normal_side is NormalSide.CREDIT


def test_account_delegates_normal_side_to_type() -> None:
    assert CASH.normal_side is NormalSide.DEBIT
    assert EQUITY.normal_side is NormalSide.CREDIT


@pytest.mark.parametrize("code", ["", "   "])
def test_blank_account_code_is_refused(code: str) -> None:
    with pytest.raises(ValueError, match="code"):
        Account(code, "Cash", AccountType.ASSET)


@pytest.mark.parametrize("name", ["", "   "])
def test_blank_account_name_is_refused(name: str) -> None:
    with pytest.raises(ValueError, match="name"):
        Account("1000", name, AccountType.ASSET)


# --------------------------------------------------------------------------- #
# Balanced entries accepted; totals exact.                                     #
# --------------------------------------------------------------------------- #


def test_balanced_entry_is_accepted_and_totals_are_exact() -> None:
    entry = JournalEntry("invest", (_deb(CASH, "10000.00"), _cre(EQUITY, "10000.00")))
    assert entry.total_debits() == Decimal("10000.00")
    assert entry.total_credits() == Decimal("10000.00")


def test_multi_leg_balanced_entry_is_accepted() -> None:
    # One debit split across two credits that sum to it exactly.
    entry = JournalEntry(
        "financing",
        (_deb(CASH, "15000.00"), _cre(EQUITY, "10000.00"), _cre(LOAN, "5000.00")),
    )
    assert entry.total_debits() == Decimal("15000.00")
    assert entry.total_credits() == Decimal("15000.00")


# --------------------------------------------------------------------------- #
# Fail-closed: unbalanced / malformed entries refused (boundary-exact).        #
# --------------------------------------------------------------------------- #


def test_off_by_one_cent_is_refused() -> None:
    # Just-over: credits exceed debits by exactly one cent -> must be refused.
    with pytest.raises(ValueError, match="does not balance"):
        JournalEntry("bad", (_deb(CASH, "100.00"), _cre(EQUITY, "100.01")))


def test_off_by_one_cent_under_is_refused() -> None:
    # Just-under: debits exceed credits by one cent.
    with pytest.raises(ValueError, match="does not balance"):
        JournalEntry("bad", (_deb(CASH, "100.01"), _cre(EQUITY, "100.00")))


def test_single_posting_entry_is_refused() -> None:
    with pytest.raises(ValueError, match="at least two postings"):
        JournalEntry("lonely", (_deb(CASH, "100.00"),))


def test_empty_entry_is_refused() -> None:
    with pytest.raises(ValueError, match="at least two postings"):
        JournalEntry("empty", ())


@pytest.mark.parametrize("desc", ["", "   "])
def test_blank_description_is_refused(desc: str) -> None:
    with pytest.raises(ValueError, match="description"):
        JournalEntry(desc, (_deb(CASH, "1.00"), _cre(EQUITY, "1.00")))


def test_zero_posting_amount_is_refused() -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        Posting(CASH, PostingSide.DEBIT, Decimal("0.00"))


def test_negative_posting_amount_is_refused() -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        Posting(CASH, PostingSide.DEBIT, Decimal("-1.00"))


def test_sub_cent_posting_amount_is_refused() -> None:
    # Fractional-cent precision must be refused (exact-money contract).
    with pytest.raises(ValueError, match="exactly representable"):
        Posting(CASH, PostingSide.DEBIT, Decimal("1.005"))


# --------------------------------------------------------------------------- #
# PROPERTY: any balanced posting set is accepted and its totals are equal;     #
# any one-cent imbalance is always refused. This is the invariant with teeth.  #
# --------------------------------------------------------------------------- #

_cent_amounts = st.integers(min_value=1, max_value=10_000_000).map(
    lambda cents: Decimal(cents).scaleb(-2)
)


@given(amount=_cent_amounts)
def test_property_equal_debit_credit_always_balances(amount: Decimal) -> None:
    entry = JournalEntry("p", (_deb(CASH, str(amount)), _cre(EQUITY, str(amount))))
    assert entry.total_debits() == entry.total_credits() == amount


@given(amount=_cent_amounts)
def test_property_any_one_cent_imbalance_is_refused(amount: Decimal) -> None:
    over = amount + Decimal("0.01")
    with pytest.raises(ValueError, match="does not balance"):
        JournalEntry("p", (_deb(CASH, str(amount)), _cre(EQUITY, str(over))))


@given(
    debits=st.lists(_cent_amounts, min_size=1, max_size=6),
    splits=st.integers(min_value=1, max_value=5),
)
def test_property_balanced_multi_leg_entry_accepted(
    debits: list[Decimal], splits: int
) -> None:
    # Build a balanced entry: total debits == total credits by construction.
    total = sum(debits, start=Decimal("0.00"))
    debit_postings = tuple(_deb(CASH, str(d)) for d in debits)
    # Credit the same total back, split across `splits` equal-ish legs using the
    # exact allocator so credits sum to exactly `total` (no cent lost).
    from autofirm.foundation.money.exact_money_arithmetic import allocate

    credit_parts = [p for p in allocate(total, [1] * splits) if p > Decimal("0.00")]
    credit_postings = tuple(_cre(EQUITY, str(p)) for p in credit_parts)
    entry = JournalEntry("p", debit_postings + credit_postings)
    assert entry.total_debits() == entry.total_credits() == total
