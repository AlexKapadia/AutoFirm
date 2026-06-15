# SUMMARY — EU AI Act (Regulation 2024/1689), Article 12: Record-keeping

## Full citation
- **Title:** Regulation (EU) 2024/1689 (Artificial Intelligence Act) — Article 12 "Record-keeping"; related Article 19 (automatically generated logs) and Article 26(6) (deployer log retention).
- **Author/Org:** European Parliament and Council of the European Union.
- **Year:** 2024 (in force; high-risk obligations apply from 2 August 2026).
- **Venue:** Official Journal of the EU; consolidated text.
- **URL:** https://artificialintelligenceact.eu/article/12/

## Question(s) informed
- **L1.A6.2** Immutable append-only audit logs (the regulatory *requirement* for lifetime logging).
- **L1.A6.3** Governance telemetry (logs enabling post-market monitoring / risk identification).

## GRADE tier
**High.** Binding EU primary legislation (regulatory standard). The authoritative legal requirement AutoFirm must satisfy for any high-risk deployment in the EU.

## Core requirement (Article 12)
High-risk AI systems "shall technically allow for the automatic recording of events (logs) over the lifetime of the system." **Automatic** = the system generates logs itself (manual documentation does not satisfy it); **lifetime** = from deployment to decommissioning.

Logging capabilities "shall enable the recording of events relevant for":
(a) identifying situations that may result in the system "presenting a risk" or in "a substantial modification";
(b) facilitating **post-market monitoring**;
(c) monitoring the operation of the high-risk AI system.

## Minimum logging for biometric systems (Annex III point 1(a))
At minimum: usage period (start/end date+time); the reference database against which input data was checked; the input data for which the search led to a match; the identity of the natural persons involved in verifying the results.

## Retention
Article 26(6) requires deployers to keep the automatically generated logs "for a period appropriate to the intended purpose… at least six months" (subject to other law). Article 19 obliges providers to keep logs under their control.

## Reproducibility note
Requirement text and (a)/(b)/(c) purposes quoted/paraphrased from Article 12 at the URL; biometric minimum-logging items from Art. 12(3); retention from Art. 26(6). Re-derive from the consolidated Regulation 2024/1689.
