# W5 / B5-09 — Multi-Currency & Money Representation Standards

**Workstream:** W5 — 100%-accurate cross-model spend/cost accounting.
**Research question:** How must money be represented across currencies so that precision is currency-correct, allocations lose no penny, and FX conversions are auditable and reproducible?
**Date accessed:** 2026-06-17.

---

## 1. Full Citations

1. **ISO — ISO 4217 Currency codes.** International Organization for Standardization. URL: https://www.iso.org/iso-4217-currency-codes.html — accessed 2026-06-17. **GRADE: High** (the standard itself). NOTE: the iso.org page returned **HTTP 403** to automated fetch this pass — the minor-unit facts below are corroborated from ISO 4217 secondary references (Adyen, Wikipedia ISO 4217); the standard's existence and scope are **unverified by direct fetch** and should be confirmed against the published standard.
2. **Adyen Docs — Currency codes and minor units.** URL: https://docs.adyen.com/development-resources/currency-codes/ — accessed 2026-06-17. **GRADE: Medium-High** (a payments processor's published ISO-4217 minor-unit table; professional/primary for the exponent values).
3. **Wikipedia — ISO 4217.** URL: https://en.wikipedia.org/wiki/ISO_4217 — accessed 2026-06-17. **GRADE: Medium** (corroborating; cites the standard).
4. **Martin Fowler — Money (pattern).** *Patterns of Enterprise Application Architecture*, Ch. 18; catalog entry. URL: https://martinfowler.com/eaaCatalog/money.html — accessed 2026-06-17. **GRADE: High** (canonical software-design primary source). NOTE: the catalog page gives the *problem statement* verbatim; the full allocation algorithm lives in the book chapter and is **summarized from record, not fetched verbatim** this pass.
5. **Oracle (OIPA / NetSuite) documentation — original-currency storage & FX audit.** URL: https://docs.oracle.com/cd/E18894_01/rules_palette/Content/Prototypes/Original%20Currency%20Detail.htm — accessed 2026-06-17. **GRADE: Medium-High** (enterprise-system primary source on storing original currency + rate + effective date).

---

## 2. Faithful Structured Summary

### 2.1 ISO 4217 — codes AND the minor unit

ISO 4217 defines, per currency: a **three-letter alphabetic code** (e.g. `USD`, `JPY`, `BHD`), a **three-digit numeric code**, and the **minor unit** — the number of decimal places (the *exponent*) by which the major unit subdivides. Rounding precision is therefore **currency-dependent**:

| Currency | Minor-unit exponent | Quantum (Decimal) |
|---|---|---|
| USD (US dollar) | **2** | `Decimal('0.01')` |
| EUR, GBP (most currencies) | **2** | `Decimal('0.01')` |
| JPY (Japanese yen) | **0** | `Decimal('1')` |
| BHD (Bahraini dinar), KWD, OMR | **3** | `Decimal('0.001')` |

> "The U.S. dollar (USD) has a minor unit exponent of 2 ... The Japanese yen (JPY) has no minor unit at all, with an exponent of 0 ... The Bahraini dinar (BHD) divides into 1,000 subunits rather than 100, giving it a minor unit exponent of 3." (source per search of refs 2/3)

> "ISO 4217 specifies how many decimal places each currency uses, a detail the standard calls the 'minor unit'. Most currencies divide into 100 subunits and carry two decimal places, but there are notable exceptions like JPY and BHD."

The minor-unit exponent is the authoritative input to `.quantize()` — **assuming 2 dp for all currencies is a defect** (it over-rounds BHD by one digit and invents fractional yen).

### 2.2 The "store money as integer minor units" pattern + the penny-allocation problem (Fowler, verbatim where quoted)

> "A large proportion of the computers in this world manipulate money, so it's always puzzled me that money isn't actually a first class data type in any mainstream programming language."

> "once you involve multiple currencies you want to avoid adding your dollars to your yen without taking the currency differences into account."

> "The more subtle problem is with rounding. Monetary calculations are often rounded to the smallest currency unit. When you do this it's easy to lose pennies (or your local equivalent) because of rounding errors."

> "you can fix these problems by creating a Money class that handles them."

**Money pattern essentials (from the pattern, summarized):**
- A `Money` value object carries an **amount** *and* a **currency** — the two are inseparable; arithmetic across different currencies is forbidden without explicit conversion.
- Store the amount as an **integer count of the smallest currency unit** (cents/minor units) — equivalently, a `Decimal` quantized to the currency's minor unit. Both avoid binary-float error (folder 08).
- **Allocation / largest-remainder rule:** when a sum is split (e.g. allocating a $100.00 invoice across 3 line items), naive per-share rounding loses or creates pennies. Fowler's `allocate` distributes the **remainder one minor unit at a time** to the first *N* shares so the parts **sum back to the original exactly** (no penny lost or conjured). This is the GAAP/auditor expectation: **allocations must reconcile to the total to the cent.**

### 2.3 FX conversion — store original + rate + timestamp (Oracle/enterprise practice)

FX rates carry many decimal places; converting then rounding requires a **defined rounding rule** and an **audit trail**:

> "OIPA stores the original currency code, currency amount, exchange rate effective date and exchange rate ... The system records values used in these accounting currency exchanges for auditing purposes."

> "Currency rates are always fluctuating, and whenever there is a time delay in processing payments or refunds, there is a possibility that you might lose or gain money because of currency conversions." (why the **rate timestamp** is load-bearing)

Best practice: keep **(1) original amount + original currency, (2) the exact rate used, (3) the rate's effective timestamp/source, (4) the converted amount + target currency**. Never persist *only* the converted figure — without the rate and timestamp the conversion cannot be reproduced, audited, or disputed, and the result is not deterministic against a later rate.

---

## 3. Best Parts to Take → W5 Mapping

- **`Money` value object = (Decimal amount, ISO-4217 currency).** Currency travels with the amount; cross-currency arithmetic is rejected unless an explicit, rate-stamped conversion is performed.
- **ISO-4217-aware precision:** quantize to the currency's **minor-unit exponent**, not a hard-coded 2 dp — `0.01` for USD/EUR, `1` for JPY, `0.001` for BHD. The minor-unit table is a typed, tested lookup; an unknown currency code **fails closed**, never defaults to 2.
- **Largest-remainder allocation** for any split of provider cost across models/tenants/line-items: distribute the rounding remainder unit-by-unit so the parts **sum back to the total exactly** — property-test `sum(allocate(total, weights)) == total` for all weight vectors and currencies.
- **FX `UsageCostRecord` stores original currency + amount + exact rate + rate timestamp/source + converted amount + target currency** — never the converted amount alone. Conversion uses a fixed, documented rounding mode (folder 08) so it is reproducible and auditable.
- **Determinism + boundary tests:** JPY amounts have no fractional part; BHD has three; allocation across `n` shares for non-divisible totals; round-trip A→B→A within tolerance with the recorded rate.

## 4. RED Flags

- **Assuming 2 dp for every currency** — silently wrong for JPY (0) and BHD/KWD/OMR (3); over- or under-rounds and breaks reconciliation.
- **Adding amounts of different currencies** without conversion — "adding your dollars to your yen."
- **Naive per-share rounding on splits** — loses or invents pennies; allocations must sum to the total exactly (largest-remainder).
- **Storing only the converted amount** — non-reproducible, non-auditable; always keep original + rate + timestamp.
- **Defaulting an unknown currency to 2 dp** instead of failing closed.
