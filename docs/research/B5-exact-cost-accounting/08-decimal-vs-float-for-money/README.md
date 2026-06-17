# W5 / B5-08 — Decimal vs. Float for Money: Why Binary Floating Point Must Never Hold Money

**Workstream:** W5 — 100%-accurate cross-model spend/cost accounting (zero numerical errors on deterministic money paths).
**Research question:** Why is IEEE-754 binary floating point unsafe for money, how does decimal arithmetic fix it, and exactly which rounding modes and quantization discipline must W5 use?
**Date accessed:** 2026-06-17.

---

## 1. Full Citations

1. **Python Software Foundation — `decimal` — Decimal fixed-point and floating-point arithmetic.** Python 3 Standard Library documentation. URL: https://docs.python.org/3/library/decimal.html — accessed 2026-06-17. **GRADE: High** (canonical language/standards reference; the library W5 will actually use).
2. **Python Software Foundation — Floating-Point Arithmetic: Issues and Limitations.** Python 3 Tutorial, §15. URL: https://docs.python.org/3/tutorial/floatingpoint.html — accessed 2026-06-17. **GRADE: High** (canonical; reproduces the exact IEEE-754 binary representation of 0.1).
3. **Mike Cowlishaw / IBM — General Decimal Arithmetic Specification.** URL: https://speleotrove.com/decimal/ — accessed 2026-06-17. **GRADE: High** (the standard that *is* the basis of Python `decimal`, Java `BigDecimal`, and IEEE 754-2008 decimal formats).
4. **IEEE 754-2008 / ISO/IEC/IEEE 60559:2011** (decimal floating-point formats) — referenced via source 3, which states it "describes the decimal arithmetic in the new IEEE 754 standard." Standard text is paywalled; **GRADE: High but text unverified directly** (relied on source 3's primary description).
5. **D. Goldberg — "What Every Computer Scientist Should Know About Floating-Point Arithmetic,"** ACM Computing Surveys, Vol. 23, No. 1, March 1991 — the classical primary reference for binary FP representation error. Not fetched this pass; **cited from record, text unverified directly.**

---

## 2. Faithful Structured Summary

### 2.1 Why binary float cannot hold decimal money (source 2, verbatim)

> "Unfortunately, most decimal fractions cannot be represented exactly as binary fractions. A consequence is that, in general, the decimal floating-point numbers you enter are only approximated by the binary floating-point numbers actually stored in the machine."

> "In base 2, 1/10 is the infinitely repeating fraction 0.0001100110011001100110011001100110011001100110011..."

The exact stored value of the literal `0.1` is **not** one tenth:

> "the exact number stored in the computer is equal to the decimal value 0.1000000000000000055511151231257827021181583404541015625"

> "On most machines today, floats are approximated using a binary fraction with the numerator using the first 53 bits ... In the case of 1/10, the binary fraction is `3602879701896397 / 2 ** 55` which is close to but not exactly equal to the true value of 1/10."

Consequence (the canonical money bug):

```text
>>> 0.1 + 0.1 + 0.1 == 0.3
False
```

### 2.2 How decimal fixes it (source 1, verbatim)

> "Decimal numbers can be represented exactly. In contrast, numbers like `1.1` and `2.2` do not have exact representations in binary floating point. End users typically would not expect `1.1 + 2.2` to display as `3.3000000000000003` as it does with binary floating point."

> "The exactness carries over into arithmetic. In decimal floating point, `0.1 + 0.1 + 0.1 - 0.3` is exactly equal to zero. In binary floating point, the result is `5.5511151231257827e-017`. While near to zero, the differences prevent reliable equality testing and differences can accumulate. **For this reason, decimal is preferred in accounting applications which have strict equality invariants.**"

### 2.3 Precision / context model (source 1, verbatim)

> "Each thread has its own current context which is accessed or changed using the `getcontext()` and `setcontext()` functions."

> "You can also use the `with` statement and the `localcontext()` function to temporarily change the active context."

> "Unlike hardware based binary floating point, the decimal module has a user alterable precision (defaulting to **28** places) which can be as large as needed for a given problem."

```python
from decimal import localcontext
with localcontext() as ctx:
    ctx.prec = 42        # high-precision intermediate calculation
    s = calculate_something()
s = +s                   # round final result back to default precision
```

### 2.4 Rounding modes — EXACT enumeration (source 1, verbatim table)

| Constant | Behaviour |
|---|---|
| `ROUND_CEILING` | Round towards `Infinity` |
| `ROUND_DOWN` | Round towards zero |
| `ROUND_FLOOR` | Round towards `-Infinity` |
| `ROUND_HALF_DOWN` | Round to nearest with ties going towards zero |
| `ROUND_HALF_EVEN` | Round to nearest with ties going to nearest even integer |
| `ROUND_HALF_UP` | Round to nearest with ties going away from zero |
| `ROUND_UP` | Round away from zero |
| `ROUND_05UP` | Round away from zero if last digit after rounding towards zero would have been 0 or 5; otherwise round towards zero |

**Default rounding mode (verbatim):**

> "The default values are `Context.prec`=`28`, `Context.rounding`=`ROUND_HALF_EVEN`"

`ROUND_HALF_EVEN` is **banker's rounding** — ties go to the nearest even digit. It is the default precisely because it is unbiased over many rounding operations (positive and negative bias cancel), which keeps accumulated drift near zero across a large ledger. `ROUND_HALF_UP` ("ties away from zero") is the "schoolbook" mode some invoices/jurisdictions require — it must be chosen *explicitly* and documented, never assumed.

### 2.5 `quantize()` — fixed-point money rounding (source 1, verbatim)

> "Return a value equal to the first operand after rounding and having the exponent of the second operand."

> "If the exponent of the second operand is larger than that of the first then rounding may be necessary. In this case, the rounding mode is determined by the `rounding` argument if given, else by the given `context` argument; if neither argument is given the rounding mode of the current thread's context is used."

```python
>>> Decimal('1.41421356').quantize(Decimal('1.000'))
Decimal('1.414')
>>> TWOPLACES = Decimal(10) ** -2       # same as Decimal('0.01')
>>> Decimal('3.214').quantize(TWOPLACES)
Decimal('3.21')
```

`.quantize(Decimal('0.01'))` is the operation that pins a value to exactly 2 decimal places (cents). For W5, the quantum is **currency-dependent**, not always `0.01` (see folder 09).

### 2.6 Standards lineage (sources 1 & 3, verbatim)

> "This is a standard context defined by the General Decimal Arithmetic Specification." (source 1)

> "This specification forms the basis for a number of implementations, and also describes the decimal arithmetic in the new IEEE 754 standard." (source 3)

> "Up to a given working precision, exact unrounded results are given when possible (for instance, 0.9 ÷ 10 gives 0.09, not 0.089999996), and trailing zeros are correctly preserved in most operations." (source 3 — design principle: "arithmetic that works in the same way as the arithmetic that people learn at school")

Lineage: Python `decimal` (Stefan Krah's libmpdec from 3.3 onward) implements Cowlishaw's General Decimal Arithmetic Specification, which is also the basis of IEEE 754-2008 / ISO-IEC-IEEE 60559:2011 decimal formats and Java 5 `BigDecimal`.

---

## 3. Best Parts to Take → W5 Mapping

- **`Decimal`, never `float`, on every money path.** Construct from `str` or `int` (`Decimal('0.10')`), never from a `float` literal (`Decimal(0.1)` inherits the binary error). Floats only ever appear in non-money analytics.
- **Decision: `ROUND_HALF_EVEN` (banker's) as the W5 default**, matching the `decimal` default — unbiased accumulation across a large usage ledger. Any path requiring a different mode (e.g. a provider invoice that uses `ROUND_HALF_UP`) sets it **explicitly** via the `rounding=` argument and records which mode was used.
- **Always `.quantize()` to the currency minor unit before persisting or comparing** — never compare un-quantized intermediates. Quantum comes from the ISO-4217 minor-unit exponent (folder 09), e.g. `Decimal('0.01')` for USD, `Decimal('1')` for JPY.
- **Keep full precision through intermediate math** (use `localcontext()` with raised `prec` for multi-step rate math), quantize **once** at the boundary — quantizing mid-calculation injects avoidable rounding error.
- **Determinism tests:** assert `0.1 + 0.1 + 0.1 - 0.3 == 0` in Decimal; property-test that quantize is idempotent and that mode is fixed; mutation-test the rounding constant so that swapping `ROUND_HALF_EVEN`→`ROUND_HALF_UP` is caught by a test.

## 4. RED Flags

- **`float` for money = silent drift** — `0.1 + 0.2 != 0.3`; errors accumulate and "prevent reliable equality testing" (the exact failure mode that breaks a ledger's equality invariants).
- **`Decimal(0.1)` from a float** — silently imports the binary error; always pass a string.
- **Relying on the implicit default rounding mode without asserting it** — a context change elsewhere could flip it; pin and test it.
- **Quantizing intermediates / comparing un-quantized values** — manufactures off-by-a-cent mismatches.
