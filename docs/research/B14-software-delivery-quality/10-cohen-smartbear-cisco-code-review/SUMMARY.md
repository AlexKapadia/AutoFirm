# SUMMARY — Cisco/SmartBear Code-Review Study (Best Kept Secrets of Peer Code Review)

## Full citation
- **Title:** Best Kept Secrets of Peer Code Review (Cisco Systems case study)
- **Author/Org:** Jason Cohen et al., SmartBear Software
- **Year:** 2006 (book) + ongoing SmartBear "Best Practices for Peer Code Review"
- **Venue:** SmartBear Software (practitioner book + study report)
- **URL:** https://smartbear.com/learn/code-review/best-practices-for-peer-code-review/

## Questions it informs
- **L1.B14.3** (code review as a maintainability/quality control; objective limits on review chunk size).

## Method and scale (exact)
- A **10-month study of ~2,500 code reviews covering 3.2 million lines of code at Cisco Systems** (one of the largest empirical code-review studies).

## Key findings (exact, practitioner thresholds)
1. **Review fewer than 200-400 LOC at a time.** Above ~400 LOC, defect-detection ability drops off sharply (reviewers start to miss defects).
2. **Inspection rate** should be **under ~300-500 LOC per hour**; faster review misses a significant fraction of defects.
3. **Total review session ~60 minutes, not exceeding ~90 minutes** - detection rates fall after 60-90 minutes of continuous review.
4. Observed **defect density averaged ~32 defects per 1,000 LOC**; 61% of reviews found no defects, and the rest ranged ~10-130 defects/kLOC.

## GRADE tier
**Low-Moderate.** Large-scale industrial study but vendor-authored (SmartBear sells review tooling) and not peer-reviewed - down-rated for risk of bias. The chunk-size and rate thresholds are corroborated by independent practitioner replication and align with inspection research (Fagan inspections), so used as directional design guidance, not a hard law.

## Reproducibility note
The 2,500-reviews / 3.2M-LOC / 200-400-LOC / 60-min figures are consistently reported across SmartBear materials and independent summaries (Mike Conley write-up). Treat the numeric thresholds as practitioner heuristics with a known commercial source bias.
