# BEST-PARTS — SaaS Operating-Model Metrics

## What AutoFirm ADOPTS

1. **The SaaS metric stack is AutoFirm's operating-model template for recurring-revenue digital
   companies (panel row 1, and any subscription business).** When AutoFirm builds/operates a SaaS
   client, it instantiates: Rule of 40, NRR, CAC payback, Magic Number, Burn Multiple, LTV/CAC as
   the standing KPI contract — the SaaS analogue of SCOR's five attributes for physical ops.
   - **Build implication:** L2.B4's modeling toolkit ships these as deterministic formulae
     (computed exactly from revenue/cost inputs — CLAUDE.md §3.11 zero numerical errors); L2.B5
     pricing optimizes against them.

2. **Formulae are deterministic and unit-exact -> perfect for the deterministic core.** Every metric
   above is a closed-form arithmetic identity. These belong in AutoFirm's auditable deterministic
   layer with property/boundary tests (e.g. NRR at 100%, churn=expansion edge), not an ML layer.

3. **Benchmarks are CONFIGURABLE INPUTS, never magic constants.** "40", "3x LTV/CAC", "12-month
   payback" are *contingent thresholds* that move by stage/year/segment. AutoFirm stores them as
   versioned, cited config (which survey, which year), satisfying generality (§3.9) and exact
   citation (§3.3).
   - **Build implication:** a `benchmarks.yaml` with `{metric, threshold, source, year}` provenance;
     the engine compares a client's computed metric to the cited band, and the explanation names the
     source — never asserts a bare number.

## What AutoFirm REJECTS / caution
- **Reject hard-coding any benchmark number into logic.** Doing so overfits to one market snapshot.
- **Reject single-metric optimization.** Rule of 40 deliberately *balances* two forces; optimizing
  growth alone or margin alone is the classic failure. The playbook must reason over the full stack.
- Caution: attribute Rule of 40 to **both Fred Wilson and Brad Feld (2015)**; do not present a
  single inventor as settled fact (citation honesty).

## Quantification for evidence/
- A SaaS scorecard (6 metrics) computed from real *public* SaaS filings (10-K/10-Q of public SaaS
  cos) for the §3.12 public-data validation — proves the formulae compute correctly on real data.
- Sensitivity charts: Rule-of-40 / payback as functions of churn and CAC — demonstrates the engine's
  modeling, feeds evidence/.
