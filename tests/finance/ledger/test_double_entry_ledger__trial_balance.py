"""Adversarial + property tests for the ledger's balances and trial balance.

The defining global invariant: after posting any sequence of (individually
balanced) journal entries, the trial balance is EXACTLY zero. The property test
generates arbitrary valid entry sequences and asserts the trial balance is
``Decimal("0.00")`` every time, and that signed balances respect the normal-side
convention. Designed to KILL mutants on ``double_entry_ledger``.
"""

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from autofirm.finance.ledger.account_types import Account, AccountType
from autofirm.finance.ledger.double_entry_ledger import DoubleEntryLedger, _signed_delta
from autofirm.finance.ledger.journal_entry import JournalEntry, Posting, PostingSide

CASH = Account("1000", "Cash", AccountType.ASSET)
EQUIP = Account("1500", "Equipment", AccountType.ASSET)
LOAN = Account("2000", "Bank Loan", AccountType.LIABILITY)
EQUITY = Account("3000", "Common Stock", AccountType.EQUITY)
REVENUE = Account("4000", "Sales", AccountType.REVENUE)
EXPENSE = Account("5000", "Rent", AccountType.EXPENSE)


def _deb(a: Account, m: str) -> Posting:
    return Posting(a, PostingSide.DEBIT, Decimal(m))


def _cre(a: Account, m: str) -> Posting:
    return Posting(a, PostingSide.CREDIT, Decimal(m))


def test_signed_delta_increases_on_normal_side() -> None:
    # Debit to a debit-normal account increases it; credit decreases it.
    assert _signed_delta(PostingSide.DEBIT, CASH.normal_side, Decimal("5.00")) == Decimal("5.00")
    assert _signed_delta(PostingSide.CREDIT, CASH.normal_side, Decimal("5.00")) == Decimal("-5.00")
    # Credit to a credit-normal account increases it; debit decreases it.
    assert _signed_delta(PostingSide.CREDIT, EQUITY.normal_side, Decimal("5.00")) == Decimal("5.00")
    assert _signed_delta(PostingSide.DEBIT, EQUITY.normal_side, Decimal("5.00")) == Decimal("-5.00")


def test_empty_ledger_trial_balance_is_zero() -> None:
    assert DoubleEntryLedger().trial_balance() == Decimal("0.00")


def test_untouched_account_has_zero_balance() -> None:
    ledger = DoubleEntryLedger()
    assert ledger.balance_of(CASH) == Decimal("0.00")


def test_worked_example_balances_and_trial_balance_zero() -> None:
    ledger = DoubleEntryLedger()
    ledger.post(JournalEntry("invest", (_deb(CASH, "10000.00"), _cre(EQUITY, "10000.00"))))
    ledger.post(JournalEntry("sale", (_deb(CASH, "500.00"), _cre(REVENUE, "500.00"))))
    ledger.post(JournalEntry("rent", (_deb(EXPENSE, "200.00"), _cre(CASH, "200.00"))))
    # Cash = 10000 + 500 - 200 = 10300; exact to the cent.
    assert ledger.balance_of(CASH) == Decimal("10300.00")
    assert ledger.balance_of(EQUITY) == Decimal("10000.00")
    assert ledger.balance_of(REVENUE) == Decimal("500.00")
    assert ledger.balance_of(EXPENSE) == Decimal("200.00")
    assert ledger.trial_balance() == Decimal("0.00")


def test_entry_log_is_append_only_and_ordered() -> None:
    ledger = DoubleEntryLedger()
    e1 = JournalEntry("a", (_deb(CASH, "1.00"), _cre(EQUITY, "1.00")))
    e2 = JournalEntry("b", (_deb(CASH, "2.00"), _cre(EQUITY, "2.00")))
    ledger.post(e1)
    ledger.post(e2)
    assert ledger.entries() == (e1, e2)


def test_repeated_posting_accumulates_exactly() -> None:
    ledger = DoubleEntryLedger()
    for _ in range(3):
        ledger.post(JournalEntry("p", (_deb(CASH, "0.01"), _cre(REVENUE, "0.01"))))
    assert ledger.balance_of(CASH) == Decimal("0.03")
    assert ledger.balance_of(REVENUE) == Decimal("0.03")
    assert ledger.trial_balance() == Decimal("0.00")


# --------------------------------------------------------------------------- #
# PROPERTY: arbitrary valid entry sequence -> trial balance ALWAYS zero.       #
# --------------------------------------------------------------------------- #

_ACCOUNTS = [CASH, EQUIP, LOAN, EQUITY, REVENUE, EXPENSE]
_cents = st.integers(min_value=1, max_value=1_000_000).map(lambda c: Decimal(c).scaleb(-2))


@st.composite
def _balanced_entry(draw: st.DrawFn) -> JournalEntry:
    """Generate a random but always-balanced two-leg journal entry."""
    amount = draw(_cents)
    debit_account = draw(st.sampled_from(_ACCOUNTS))
    credit_account = draw(st.sampled_from(_ACCOUNTS))
    return JournalEntry(
        "p",
        (
            Posting(debit_account, PostingSide.DEBIT, amount),
            Posting(credit_account, PostingSide.CREDIT, amount),
        ),
    )


@given(entries=st.lists(_balanced_entry(), min_size=0, max_size=40))
def test_property_trial_balance_always_zero(entries: list[JournalEntry]) -> None:
    ledger = DoubleEntryLedger()
    for entry in entries:
        ledger.post(entry)
    # No matter the sequence of balanced entries, debits-minus-credits nets to 0.
    assert ledger.trial_balance() == Decimal("0.00")


@given(entries=st.lists(_balanced_entry(), min_size=1, max_size=40))
def test_property_sum_of_signed_normal_balances_consistent(
    entries: list[JournalEntry],
) -> None:
    ledger = DoubleEntryLedger()
    for entry in entries:
        ledger.post(entry)
    # Re-derive trial balance independently from per-account balances: must be 0.
    from autofirm.finance.ledger.account_types import NormalSide

    total = Decimal("0.00")
    for account in ledger.accounts():
        bal = ledger.balance_of(account)
        total += bal if account.normal_side is NormalSide.DEBIT else -bal
    assert total == Decimal("0.00")
