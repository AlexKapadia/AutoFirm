"""Property + worked-example tests for the three-statement articulation.

These are the branch's highest-value tests (SYNTHESIS §1): generate internally-
consistent random ledgers and assert ALL cross-statement invariants hold to the
cent over arbitrary valid transaction sequences:

* debits == credits (enforced upstream; here we build only balanced entries),
* Balance Sheet ALWAYS balances: Assets = Liabilities + Equity,
* net income == revenue - expenses, and FLOWS into retained earnings,
* Cash-Flow net change ALWAYS ties to the Balance-Sheet cash delta.

Plus a labelled golden set of hand-computed worked examples proving ZERO
numerical error to the cent. Designed to KILL mutants across all statement modules.
"""

from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from autofirm.finance.ledger.account_types import Account, AccountType
from autofirm.finance.ledger.double_entry_ledger import DoubleEntryLedger
from autofirm.finance.ledger.journal_entry import JournalEntry, Posting, PostingSide
from autofirm.finance.statements.balance_sheet import BalanceSheet
from autofirm.finance.statements.cash_flow_statement import CashFlowStatement
from autofirm.finance.statements.income_statement import IncomeStatement

# A fixed synthetic chart of accounts (public-style figures, no real PII).
CASH = Account("1000", "Cash", AccountType.ASSET)
EQUIP = Account("1500", "Equipment", AccountType.ASSET)
LOAN = Account("2000", "Bank Loan", AccountType.LIABILITY)
EQUITY = Account("3000", "Common Stock", AccountType.EQUITY)
REVENUE = Account("4000", "Sales Revenue", AccountType.REVENUE)
EXPENSE = Account("5000", "Operating Expense", AccountType.EXPENSE)
CASH_CODES = frozenset({"1000"})


def _deb(a: Account, m: str) -> Posting:
    return Posting(a, PostingSide.DEBIT, Decimal(m))


def _cre(a: Account, m: str) -> Posting:
    return Posting(a, PostingSide.CREDIT, Decimal(m))


# --------------------------------------------------------------------------- #
# GOLDEN SET — hand-computed worked examples, exact to the cent.               #
# --------------------------------------------------------------------------- #


def _seed_worked_ledger() -> DoubleEntryLedger:
    """A multi-transaction firm with hand-verifiable statement figures."""
    ledger = DoubleEntryLedger()
    ledger.post(JournalEntry("invest", (_deb(CASH, "10000.00"), _cre(EQUITY, "10000.00"))))
    ledger.post(JournalEntry("loan", (_deb(CASH, "5000.00"), _cre(LOAN, "5000.00"))))
    ledger.post(JournalEntry("buy equip", (_deb(EQUIP, "4000.00"), _cre(CASH, "4000.00"))))
    ledger.post(JournalEntry("cash sale", (_deb(CASH, "3000.00"), _cre(REVENUE, "3000.00"))))
    ledger.post(JournalEntry("pay opex", (_deb(EXPENSE, "1200.00"), _cre(CASH, "1200.00"))))
    return ledger


def test_golden_income_statement_exact() -> None:
    inc = IncomeStatement.from_ledger(_seed_worked_ledger())
    assert inc.total_revenue == Decimal("3000.00")
    assert inc.total_expenses == Decimal("1200.00")
    # net income = 3000 - 1200 = 1800, exact to the cent.
    assert inc.net_income() == Decimal("1800.00")


def test_golden_balance_sheet_exact_and_balances() -> None:
    bs = BalanceSheet.from_ledger(_seed_worked_ledger())
    # Cash 12800 (10000+5000-4000+3000-1200) + Equipment 4000 = 16800 assets.
    assert bs.total_assets == Decimal("16800.00")
    assert bs.total_liabilities == Decimal("5000.00")
    assert bs.contributed_equity == Decimal("10000.00")
    assert bs.retained_earnings == Decimal("1800.00")  # net income flows in
    # Equity = 10000 + 1800 = 11800; L + E = 5000 + 11800 = 16800 == assets.
    assert bs.total_equity() == Decimal("11800.00")
    assert bs.total_assets == bs.total_equity_and_liabilities()


def test_golden_cash_flow_exact_and_ties() -> None:
    ledger = _seed_worked_ledger()
    cfs = CashFlowStatement.from_ledger(ledger, CASH_CODES)
    # operating: +3000 sale - 1200 opex = 1800; investing: -4000 equipment;
    # financing: +10000 equity + 5000 loan = 15000.
    assert cfs.operating == Decimal("1800.00")
    assert cfs.investing == Decimal("-4000.00")
    assert cfs.financing == Decimal("15000.00")
    # net = 1800 - 4000 + 15000 = 12800 == change in cash balance, to the cent.
    assert cfs.net_change() == Decimal("12800.00")
    assert cfs.net_change() == ledger.balance_of(CASH)


def test_net_income_flows_to_retained_earnings_exactly() -> None:
    ledger = _seed_worked_ledger()
    inc = IncomeStatement.from_ledger(ledger)
    bs = BalanceSheet.from_ledger(ledger)
    # The articulation link: retained earnings on the BS == net income on the IS.
    assert bs.retained_earnings == inc.net_income()


# --------------------------------------------------------------------------- #
# PROPERTY — arbitrary internally-consistent ledgers: ALL invariants hold.     #
# --------------------------------------------------------------------------- #

_cents = st.integers(min_value=1, max_value=2_000_000).map(lambda c: Decimal(c).scaleb(-2))


@st.composite
def _consistent_transactions(draw: st.DrawFn) -> list[JournalEntry]:
    """Generate a list of balanced, internally-consistent business transactions.

    Each transaction is one of a small set of *realistic* two-leg events drawn
    from the fixed chart of accounts, so every generated ledger is a plausible
    firm — never a degenerate one. All entries balance by construction.
    """
    n = draw(st.integers(min_value=0, max_value=25))
    entries: list[JournalEntry] = []
    for _ in range(n):
        kind = draw(st.integers(min_value=0, max_value=5))
        amount = str(draw(_cents))
        if kind == 0:  # owner invests cash (financing)
            entries.append(JournalEntry("invest", (_deb(CASH, amount), _cre(EQUITY, amount))))
        elif kind == 1:  # take a loan (financing)
            entries.append(JournalEntry("loan", (_deb(CASH, amount), _cre(LOAN, amount))))
        elif kind == 2:  # buy equipment for cash (investing)
            entries.append(JournalEntry("buy", (_deb(EQUIP, amount), _cre(CASH, amount))))
        elif kind == 3:  # cash sale (operating)
            entries.append(JournalEntry("sale", (_deb(CASH, amount), _cre(REVENUE, amount))))
        elif kind == 4:  # pay an expense in cash (operating)
            entries.append(JournalEntry("opex", (_deb(EXPENSE, amount), _cre(CASH, amount))))
        else:  # repay loan principal with cash (financing)
            entries.append(JournalEntry("repay", (_deb(LOAN, amount), _cre(CASH, amount))))
    return entries


@settings(max_examples=300)
@given(transactions=_consistent_transactions())
def test_property_balance_sheet_always_balances(
    transactions: list[JournalEntry],
) -> None:
    ledger = DoubleEntryLedger()
    for entry in transactions:
        ledger.post(entry)
    # BalanceSheet.from_ledger raises fail-closed if A != L + E, so a successful
    # build IS the proof; we additionally assert the identity explicitly.
    bs = BalanceSheet.from_ledger(ledger)
    assert bs.total_assets == bs.total_equity_and_liabilities()
    assert ledger.trial_balance() == Decimal("0.00")


@settings(max_examples=300)
@given(transactions=_consistent_transactions())
def test_property_net_income_equals_revenue_minus_expenses(
    transactions: list[JournalEntry],
) -> None:
    ledger = DoubleEntryLedger()
    for entry in transactions:
        ledger.post(entry)
    inc = IncomeStatement.from_ledger(ledger)
    assert inc.net_income() == inc.total_revenue - inc.total_expenses


@settings(max_examples=300)
@given(transactions=_consistent_transactions())
def test_property_net_income_flows_to_retained_earnings(
    transactions: list[JournalEntry],
) -> None:
    ledger = DoubleEntryLedger()
    for entry in transactions:
        ledger.post(entry)
    inc = IncomeStatement.from_ledger(ledger)
    bs = BalanceSheet.from_ledger(ledger)
    assert bs.retained_earnings == inc.net_income()


@settings(max_examples=300)
@given(transactions=_consistent_transactions())
def test_property_cash_flow_net_ties_to_balance_sheet_cash_delta(
    transactions: list[JournalEntry],
) -> None:
    ledger = DoubleEntryLedger()
    for entry in transactions:
        ledger.post(entry)
    cfs = CashFlowStatement.from_ledger(ledger, CASH_CODES)
    # The cross-statement tie: net cash change == the cash balance on the BS.
    assert cfs.net_change() == ledger.balance_of(CASH)
    assert cfs.net_change() == cfs.operating + cfs.investing + cfs.financing
