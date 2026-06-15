# SUMMARY — SCOR (Supply Chain Operations Reference) Model

## Full citation
- **Title:** *Supply Chain Operations Reference (SCOR) Model* — and *SCOR Digital Standard (SCOR-DS)*
- **Owner/Author:** Supply Chain Council (founded 1996; framework developed with PRTM [now PwC] and
  AMR Research [now Gartner]); since 2014 owned by **APICS**, now **ASCM** (Association for Supply
  Chain Management).
- **Key versions:** SCOR v12.0 (2017); **SCOR Digital Standard** released 2019, updated 2022.
- **Year:** 1996 (origin) → 2022 (SCOR-DS current).
- **Venue/Publisher:** ASCM / APICS (standard body publication).
- **Primary URLs:** https://www.apics.org/apics-for-business/frameworks/scor/ ;
  SCOR-DS intro PDF — https://www.ascm.org/globalassets/ascm_website_assets/docs/intro-and-front-matter-scor-digital-standard.pdf ;
  SCOR v12.0 framework intro — http://www.apics.org/docs/default-source/scor-training/scor-v12-0-framework-introduction.pdf
- **Metrics reference:** APICS SCOR Metrics — http://www.apics.org/apics-for-business/benchmarking/scormark-process/scor-metrics

## Ontology questions informed
- **L1.B11.1** (primary): supply/delivery framework. Feeds **L2.B11** and **L2.B4** (ops modeling).

## GRADE tier
- **High** for the framework structure (it IS the cross-industry standard; the citation of record is
  the ASCM/APICS standard document, not a blog). Corroborated by APICS, ASCM, CIPS, CIO independently.
- **Down-rate:** specific benchmark *numbers* (SCORmark) are proprietary/behind certification —
  treat metric *definitions* as High, specific benchmark values as not-verified-here (omit).

## Key claims (faithful)

### Six top-level (Level-1) management processes (SCOR v12.0)
- **Plan** — "balance aggregate demand and supply to develop a course of action that best meets
  sourcing, production, and delivery requirements."
- **Source** — "procure goods and services to meet planned or actual demand."
- **Make** — "transform product to a finished state to meet planned or actual demand."
- **Deliver** — "provide finished goods and services... typically including order management,
  transportation management, and distribution management."
- **Return** — "returning or receiving returned products... extend into post-delivery customer support."
- **Enable** — "management of the supply chain": business rules, performance, data, resources,
  facilities, contracts, network management, regulatory compliance, and risk management.

> **SCOR-DS 2022 relabeling** (the "infinity loop"): Plan, **Order**, **Source**, **Transform**,
> **Fulfill**, Return, **Orchestrate**. (Transform ≈ Make; Order+Fulfill ≈ Deliver; Orchestrate ≈ Enable.)

### Hierarchical levels
- **Level 1** — scope & configuration (the processes above; strategic metrics).
- **Level 2** — configuration / process-type.
- **Level 3** — process-element detail.
- SCOR links **processes + performance metrics + practices + people skills** into one structure.

### Five performance attributes (metrics are organized under these)
1. **Reliability** (customer-focused) — e.g. **Perfect Order Fulfillment**.
2. **Responsiveness** (customer-focused) — order-to-delivery cycle times (e.g. Order Fulfillment Cycle Time).
3. **Agility** (customer-focused) — ramp-up speed / adaptability to mix/volume change.
4. **Cost** (internal) — total cost to serve / operating expense.
5. **Asset Management Efficiency** (internal) — inventory turns, capacity use, **Cash-to-Cash Cycle Time**.
- First three are **customer-facing**; last two are **internal-facing**.
- "More than 150" (v12) / "over 250" (per APICS metrics page) KPIs, hierarchically codified L1→L2→L3.

## Reproducibility note
Re-derive process definitions verbatim from the SCOR v12.0 framework-introduction PDF and the
ASCM SCOR-DS intro PDF; attributes from the APICS SCOR-metrics page. All three cited above.
