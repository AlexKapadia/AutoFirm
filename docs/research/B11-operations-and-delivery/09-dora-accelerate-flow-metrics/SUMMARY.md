# SUMMARY — DORA / Accelerate Software-Delivery Operations Metrics

## Full citation
- **Primary (book):** Forsgren, N., Humble, J., Kim, G. (2018). *Accelerate: The Science of Lean
  Software and DevOps — Building and Scaling High Performing Technology Organizations.* IT Revolution
  Press. ISBN 978-1-942788-33-1.
- **Primary (peer-reviewed roots):** Forsgren, N. & Humble, J. (2016). *The Role of Continuous
  Delivery in IT and Organizational Performance.* Proceedings of the Western Decision Sciences
  Institute (WDSI). (And the annual State of DevOps Reports / DORA program.)
- **Official program:** Google Cloud DORA — https://dora.dev/guides/dora-metrics/ ; Google Cloud
  blog "Use Four Keys metrics" — https://cloud.google.com/blog/products/devops-sre/using-the-four-keys-to-measure-your-devops-performance
- **Corroborating:** Annual *Accelerate State of DevOps Report* (Google Cloud / DORA, 2019–2024).

## Ontology questions informed
- **L1.B11.1** (primary, *delivery* operations for software/services). Feeds **L2.B11** and
  **L2.B14** (client software-delivery engine).

## GRADE tier
- **Moderate-to-High.** The four metrics and the speed/stability findings come from a multi-year,
  large-N survey research program (tens of thousands of respondents) with peer-reviewed roots
  (Forsgren/Humble) and a stated methodology (cluster analysis, PLS-SEM). **Up-rated** by replication
  across many annual reports; **down-rated** slightly because it is survey-based self-report, not
  controlled experiment.

## Key claims (faithful)

### The four key delivery metrics ("DORA Four Keys")
Two **throughput/speed** + two **stability** metrics:
1. **Deployment Frequency (DF)** — how often an org successfully releases to production.
2. **Lead Time for Changes (LT)** — time from code committed to code running in production.
3. **Change Failure Rate (CFR)** — % of deployments to production that cause a failure requiring
   remediation (rollback/hotfix/patch).
4. **(Mean) Time to Restore Service (MTTR / "Failed Deployment Recovery Time")** — how long to
   restore service after a production failure/incident.

### The central finding (speed AND stability)
The research found that **speed and stability are NOT a trade-off** — elite performers do better on
*both* simultaneously. Teams are clustered into **Elite / High / Medium / Low** performance tiers by
their four-key profile. (A fifth metric, **Reliability/operational performance**, was later added.)

### Lean lineage
*Accelerate* explicitly grounds high performance in **lean/flow principles** (small batch sizes,
WIP limits, continuous delivery, trunk-based development) — connecting directly to TPS (01), lean
(02), and Little's Law (05: small WIP → short lead time).

## Reproducibility note
The four metrics, the four performance tiers, and the speed-and-stability (not trade-off) finding are
stated in *Accelerate* (2018) and the DORA program pages cited above; methodology (cluster analysis /
PLS-SEM over State-of-DevOps survey data) is described in the book's Part II.
