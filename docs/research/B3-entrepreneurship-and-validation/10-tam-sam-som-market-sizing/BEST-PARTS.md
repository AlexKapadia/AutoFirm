# BEST-PARTS — TAM / SAM / SOM Market Sizing

## ADOPT
1. **Adopt BOTTOM-UP as AutoFirm's default, deterministic market-sizing method.**
   `Market Size = ACV x Number of Potential Customers` is exact, auditable, and grounded in real
   countable inputs — perfect for AutoFirm's deterministic core (CLAUDE SS3.5, SS3.11) and its
   public-data sourcing rule (L1.B4.4). Build implication: a `market_size_bottom_up(acv, n_customers)`
   pure function with exact unit tests (SS3.6 zero numerical errors), and the SAM/SOM derived by
   explicit, justified filters (not arbitrary percentages).
2. **Adopt the TAM/SAM/SOM nesting as a typed contract** (`MarketSizing{tam, sam, som, method,
   assumptions[], sources[]}`) where every figure carries its assumptions and public-data source —
   making each number explainable and traceable (SS3.11, SS3.13). SOM ties to the earlyvangelist
   beachhead from Customer Validation (source 04) and the JTBD competitive-alternatives (source 05).
3. **Adopt the cross-validation rule:** compute BOTH bottom-up and top-down and FLAG large
   divergence as a credibility risk (the top-down-inflation failure mode). This is an auditable
   sanity check, not a magic constant — generalizes across the industry panel.

## REJECT / DEFER
- **Reject top-down-only sizing** — multiply documented as inflated/non-credible; never AutoFirm's
  primary number. Top-down is allowed only as a cross-check / headroom narrative.
- **Reject hard-coded SOM percentages** (e.g. "assume 1-3% of SAM") as runtime constants — that is
  overfitting (SS3.9); SOM must be DERIVED from the beachhead segment + go-to-market capacity, with
  the assumptions recorded as data.
- **Defer detailed industry data-source mapping** (which registry/filing per industry) to L1.B4.4
  and L2.B4; this note fixes the *method*, B4 supplies the *data plumbing*.

## Build implication for evidence/
Market-sizing outputs feed evidence/ as labeled bottom-up vs top-down bars with stated assumptions
and sources — never a bare "$XB TAM." Determinism test: identical inputs -> identical TAM/SAM/SOM to
the unit. The divergence-flag is a quantified credibility metric across the fixed industry panel.
