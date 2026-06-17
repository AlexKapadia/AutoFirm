"""The exact, currency-aware ``Money`` value type (amount + ISO-4217 currency).

What this does
--------------
Defines :class:`Money`, the immutable pairing of an exact :class:`decimal.Decimal`
amount with an ISO-4217 currency code, plus the currency minor-unit table and the
single rounding policy (``ROUND_HALF_EVEN``) the whole platform quantises with.
``Money`` refuses ``float`` construction, refuses cross-currency addition, and
quantises to the *currency-dependent* minor unit (USD 2dp, JPY 0dp, BHD 3dp) — so
"$0.01 lost" or "summed two currencies" can never happen silently.

Why it exists / where it sits
-----------------------------
``data-contracts.md`` §8 types every cost as ``Money`` (Decimal-backed via
``exact_money_arithmetic``); the cost ledger (W5) needs an amount that *carries its
currency* so reconciliation, rollups, and quantisation are currency-correct. This
is the foundation primitive the ``costledger`` package sums and reconciles with.
It sits beside :mod:`exact_money_arithmetic` (the allocation/minor-unit helpers)
in the lowest ``foundation.money`` layer; nothing here depends on a higher package.

Security / compliance invariants upheld
---------------------------------------
* **Decimal-only, never float (CLAUDE.md §3.11, research folder 08):** a ``float``
  amount is *refused* at construction — it re-imports binary rounding error.
* **Cross-currency safety (research folder 09):** adding two different currencies
  is a refusal, never a silent coercion; a total is single-currency by construction.
* **Currency-dependent minor unit (ISO-4217, research folder 09):** quantisation
  uses the per-currency exponent; an *unknown* currency fails closed (no default 2dp).
* **Deterministic rounding:** one policy, ``ROUND_HALF_EVEN`` (banker's), applied
  once at the ledger boundary — the §3.11 determinism guarantee.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

__all__ = [
    "ISO4217_MINOR_UNIT_EXPONENT",
    "LEDGER_ROUNDING",
    "Money",
    "minor_unit_exponent",
]

# The single, platform-wide rounding policy (research folder 08: Python default,
# banker's rounding). Any deviation must be explicit and recorded — there is none.
LEDGER_ROUNDING: Final = ROUND_HALF_EVEN

# ISO-4217 minor-unit exponents (fractional digits in one major unit). The minor
# unit is currency-DEPENDENT (research folder 09): a hard-coded 2dp is WRONG for
# JPY (0) and BHD/KWD/OMR (3). This table is the authority; an unknown currency
# fails closed rather than defaulting to 2 (which would silently misquantise).
ISO4217_MINOR_UNIT_EXPONENT: Final[dict[str, int]] = {
    "USD": 2,
    "EUR": 2,
    "GBP": 2,
    "JPY": 0,  # zero-decimal currency — quantising to 2dp would invent precision
    "KRW": 0,
    "BHD": 3,  # three-decimal currency — quantising to 2dp would LOSE a unit
    "KWD": 3,
    "OMR": 3,
}


def minor_unit_exponent(currency: str) -> int:
    """Return the ISO-4217 minor-unit exponent for ``currency`` (fail-closed).

    Args:
        currency: An upper-case ISO-4217 alphabetic code (e.g. ``"USD"``).

    Returns:
        The number of fractional digits in one major unit (2 for USD, 0 for JPY,
        3 for BHD).

    Raises:
        ValueError: If ``currency`` is not a known ISO-4217 code (fail-closed:
            an unknown currency is refused, never quantised at a guessed 2dp —
            CLAUDE.md §5.6, research folder 09).
    """
    exponent = ISO4217_MINOR_UNIT_EXPONENT.get(currency)
    if exponent is None:  # fail-closed: never guess a minor unit for an unknown code
        raise ValueError(
            f"unknown ISO-4217 currency {currency!r}: refusing to guess a minor unit"
        )
    return exponent


class Money:
    """An exact, immutable (amount, currency) pair — never a bare float.

    Construction is fail-closed: the amount must be a :class:`decimal.Decimal`
    (a ``float`` is refused — research folder 08) and the currency must be a known
    ISO-4217 code. Arithmetic refuses to mix currencies. The amount is held at full
    precision; :meth:`quantize` collapses it to the currency minor unit once, at the
    ledger boundary, with the platform :data:`LEDGER_ROUNDING` policy.
    """

    __slots__ = ("_amount", "_currency")

    def __init__(self, amount: Decimal, currency: str) -> None:
        """Build ``Money`` from an exact ``Decimal`` ``amount`` and ISO-4217 ``currency``.

        Args:
            amount: The monetary amount as an exact ``Decimal``. A ``float`` (or
                any non-``Decimal``) is refused — passing a ``float`` re-imports
                IEEE-754 drift (research folder 08).
            currency: An upper-case ISO-4217 alphabetic code; validated against the
                minor-unit table (unknown ⇒ fail closed).

        Raises:
            TypeError: If ``amount`` is not a ``Decimal`` (e.g. a ``float`` or
                ``int``) — fail-closed against float money.
            ValueError: If ``amount`` is not finite, or ``currency`` is unknown.
        """
        # fail-closed: a float amount is the single most common money bug — refuse
        # it loudly at the boundary rather than rounding silently (folder 08, §3.11).
        if not isinstance(amount, Decimal):
            raise TypeError(
                f"Money amount must be a Decimal, not {type(amount).__name__} "
                "(float money is forbidden — pass Decimal('...'))"
            )
        if not amount.is_finite():  # fail-closed: NaN/Infinity are not money
            raise ValueError(f"Money amount must be finite, got {amount!r}")
        minor_unit_exponent(currency)  # fail-closed: validate the currency is known
        self._amount = amount
        self._currency = currency

    @property
    def amount(self) -> Decimal:
        """The exact, full-precision ``Decimal`` amount (not yet minor-unit-rounded)."""
        return self._amount

    @property
    def currency(self) -> str:
        """The ISO-4217 currency code this amount is denominated in."""
        return self._currency

    def quantize(self) -> Money:
        """Return a copy whose amount is rounded to this currency's minor unit.

        Quantises ONCE, at the ledger boundary, to the per-currency exponent (USD
        2dp, JPY 0dp, BHD 3dp) with :data:`LEDGER_ROUNDING` (banker's). Deferring
        the rounding to a single boundary call — rather than rounding each per-token
        product — is what keeps the cost exact to the cent (research folder 08/§3.11).
        """
        exponent = minor_unit_exponent(self._currency)
        quantum = Decimal(1).scaleb(-exponent)  # 10**-exponent, e.g. Decimal("0.01")
        return Money(self._amount.quantize(quantum, rounding=LEDGER_ROUNDING), self._currency)

    def __add__(self, other: Money) -> Money:
        """Add two same-currency amounts (full precision); refuse cross-currency.

        Raises:
            ValueError: If ``other`` is a different currency (fail-closed: a
                cross-currency sum is meaningless and is never silently coerced —
                research folder 09).
        """
        self._require_same_currency(other)
        return Money(self._amount + other._amount, self._currency)

    def __sub__(self, other: Money) -> Money:
        """Subtract a same-currency amount (full precision); refuse cross-currency.

        Raises:
            ValueError: If ``other`` is a different currency (fail-closed).
        """
        self._require_same_currency(other)
        return Money(self._amount - other._amount, self._currency)

    def _require_same_currency(self, other: Money) -> None:
        """Refuse an operation mixing two currencies (fail-closed, folder 09)."""
        if self._currency != other._currency:
            # fail-closed: cross-currency arithmetic must convert via an explicit,
            # timestamped FX rate — never an implicit add that loses the currency.
            raise ValueError(
                f"cannot combine {self._currency} with {other._currency}: "
                "convert via an explicit FX rate first"
            )

    def __eq__(self, other: object) -> bool:
        """Two ``Money`` are equal iff both currency AND exact amount match."""
        if not isinstance(other, Money):
            return NotImplemented
        return self._currency == other._currency and self._amount == other._amount

    def __hash__(self) -> int:
        """Hash over (currency, amount) so ``Money`` is usable as a dict key/set member."""
        return hash((self._currency, self._amount))

    def __repr__(self) -> str:
        """An unambiguous, reconstruction-shaped repr (amount + currency)."""
        return f"Money(Decimal('{self._amount}'), {self._currency!r})"
