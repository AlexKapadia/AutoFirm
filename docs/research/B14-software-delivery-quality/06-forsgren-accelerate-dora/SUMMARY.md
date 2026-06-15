# SUMMARY — Accelerate / DORA: CI/CD capabilities predict software delivery performance

## Full citation
- **Title:** Accelerate: The Science of Lean Software and DevOps: Building and Scaling High Performing Technology Organizations
- **Authors:** Nicole Forsgren, Jez Humble, Gene Kim
- **Year:** 2018 (IT Revolution Press); ongoing in the annual Accelerate State of DevOps Report (DORA), 2014-present
- **Venue:** Book + DORA reports (Google Cloud / DORA). Underlying methodology peer-reviewed (Forsgren et al.).
- **URL:** https://itrevolution.com/24-key-capabilities-to-drive-improvement-in-software-delivery ; https://cloud.google.com/blog/products/devops-sre/using-the-four-keys-to-measure-your-devops-performance ; https://dora.dev

## Questions it informs
- **L1.B14.1** (CI/CD pipeline design; which practices measurably improve delivery)
- **L1.B14.2** (test automation as a delivery capability).

## Method and scale (exact)
- Cross-sectional survey research over six-plus years: **30,000-plus professionals / 2,000-plus organizations** worldwide (commonly cited as over 31,000 professionals); the 2024/25 cycle draws on a survey of **over 32,000** professionals.
- Cluster analysis plus inferential statistics derived **24 key capabilities** that drive delivery performance in a statistically significant way.

## Key findings (exact)
1. **Four key delivery metrics** (DORA metrics): **Deployment Frequency**, **Lead Time for Changes** (throughput); **Change Failure Rate**, **Time to Restore Service / Failed-Deployment Recovery Time** (stability). Throughput and stability move together in elite teams (no speed-vs-stability tradeoff).
2. **Continuous Delivery capabilities** that predict performance include: **version control of all artifacts, trunk-based development, test automation, deployment automation, continuous integration, shift-left on security, and loosely coupled architecture.**
3. **Trunk-based development** predicts high performance: **fewer than 3 active branches**, branch/fork lifetimes **under 1 day** before merge, and **no code-freeze/code-lock** periods.
4. Practitioner benchmark: high performers keep **Change Failure Rate about 0-15%**.

## GRADE tier
**Moderate-to-High.** Practitioner/primary research synthesis with peer-reviewed statistical methodology; DORA reports are recognised industry primary data (large N, longitudinal). Up-rated for replication across annual cycles; causal claims rest on survey + predictive modelling (not RCT), so causal language slightly down-rated.

## Reproducibility note
The Four Keys are operationalised in Google's open-source Four Keys project; the 24 capabilities and metric definitions are published by DORA. Figures cross-checked against IT Revolution, Google Cloud, Atlassian, Octopus renderings.
