# 09 — Independent V&V and the economics of an escaped defect (Boehm & Basili)

- **Authors / org:** Barry Boehm & Victor Basili, *Software Defect Reduction Top 10 List* (IEEE
  Computer, 2001); IV&V practice per the HHS EPLC IV&V Practices Guide; Boehm cost-to-fix curve.
- **Year:** 2001 (Boehm/Basili); IV&V guidance ongoing.
- **Link:** Boehm & Basili IEEE Computer 2001; HHS EPLC IV&V guide
  (https://www.hhs.gov/sites/default/files/ocio/eplc/EPLC%20Archive%20Documents/14%20-%20IVV/eplc_ivv_practices_guide.pdf)
- **Tier:** High (primary research + professional standard).

## Faithful structured summary

**Independent V&V principle:** verification and validation performed by a party **organisationally and
managerially independent** of the development team finds defects the producer misses — independence is
the source of the value (directly analogous to Panko's self-review ceiling, 01).

**Cost-of-escaped-defect (the economic argument for a hard gate):**
- Boehm's classic finding: **fixing a defect costs ~5x-100x more the later it is caught**; finding it
  in requirements/design is cheap, finding it in production is the most expensive.
- Boehm/Basili Top-10 also note **~80% of avoidable rework comes from ~20% of defects**, and that
  **peer reviews catch ~60% of defects** — i.e. review is necessary but not sufficient alone.
- Industry "defect escape rate" benchmark: **<10% escaped is excellent, 10–20% good, 20–40%
  concerning, >40% a broken QA process.**

## Best parts to take (for our gate) and why

1. **Independence is the whole point** — the gate must be a *different* agent/process from the builder
   (CLAUDE §4.9 step 5). This is the software-engineering analogue of Panko's spreadsheet result.
2. **The cost curve justifies fail-closed strictness:** an escaped error reaching an owner/investor is
   the most expensive possible failure (reputational, not just rework), so blocking on FAIL and
   exhausting a bounded correction budget rather than shipping is economically correct.
3. **Adopt "defect escape rate" as a reported KPI:** the gate's escape rate on the golden set must be
   ~0% (we control the labels); on held-out real artifacts, target the "excellent" <10% band and
   report it in `evidence/`.
