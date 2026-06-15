# BEST-PARTS — Retail / E-commerce KPIs

## What AutoFirm ADOPTS

1. **The retail KPI set is AutoFirm's operating-model template for goods-selling clients (panel row
   4: E-commerce/DTC).** Organized in three buckets — **inventory** (turnover, GMROI, sell-through,
   DIO), **sales/store** (same-store sales, sales/sqft, AOV), **e-commerce** (conversion, cart
   abandonment, retention) — this is the digital/physical-retail analogue of SCOR's attributes and
   the SaaS stack.
   - **Build implication:** L2.B4 ships these as deterministic formulae; L2.B5 (pricing) optimizes
     gross margin against GMROI; L2.B11 (delivery) ties to fulfillment/inventory.

2. **Inventory-centric thinking for any physical-goods business.** GMROI + turnover capture the
   core retail tension (margin vs. velocity vs. capital tied up in stock). AutoFirm reasons about
   cash-to-cash through inventory exactly as SCOR's Asset Efficiency attribute (source 08) — the two
   models reconcile, which is a generalization win.

3. **Same-store sales as the organic-growth invariant.** Comparable-store growth strips out
   expansion noise — a disciplined health metric AutoFirm should prefer over raw revenue growth
   (analogous to preferring NRR over gross new-revenue in SaaS, source 09). Reusable cross-industry
   principle: *isolate organic from expansion growth.*

## What AutoFirm REJECTS / caution
- **Reject single-metric optimization (e.g. revenue-only).** Retail requires balancing margin,
  turnover, and capital — GMROI exists precisely to prevent margin-only or velocity-only myopia.
- **Reject treating benchmark numbers as constants.** Conversion rates, AOV, turnover vary hugely by
  segment/season; store as cited, versioned config (same discipline as SaaS benchmarks, source 09).
- Caution: brick-and-mortar (sales/sqft, foot traffic) vs. pure e-commerce (conversion, cart
  abandonment) need different subsets — parameterize by channel, don't force all KPIs on both.

## Quantification for evidence/
- A retail scorecard (inventory + sales + e-comm buckets) computed from a real public retailer's
  10-K (inventory, COGS, comparable-sales disclosures) for the §3.12 public-data validation.
- A margin-vs-turnover (GMROI iso-curve) chart demonstrating the pricing/inventory trade-off the
  engine reasons over.
