"""Finance & accounting suite — institution-grade, zero-numerical-error.

Produces the three core financial statements (Balance Sheet, Income Statement,
Cash-Flow Statement) deterministically from a double-entry ledger, plus DCF /
NPV / IRR valuation. Every monetary value is an exact :class:`~decimal.Decimal`
routed through ``autofirm.foundation.money.exact_money_arithmetic`` — IEEE-754
floats are never used for money (CLAUDE.md §3.11). All inputs are fail-closed.
"""
