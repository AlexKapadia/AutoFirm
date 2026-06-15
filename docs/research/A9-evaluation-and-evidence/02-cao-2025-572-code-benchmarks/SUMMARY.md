# SUMMARY — Rigor, Reliability, and Reproducibility Matter: A Decade-Scale Survey of Code Benchmarks

## Full citation
- **Title:** Rigor, Reliability, and Reproducibility Matter: A Decade-Scale Survey of 572 Code Benchmarks
- **Authors:** Jialun Cao, Yuk-Kit Chan, Zixuan Ling, Wenxuan Wang, Shuqing Li, Mingwei Liu,
  Ruixi Qiao, Yuting Han, Chaozheng Wang, Boxi Yu, Pinjia He, Shuai Wang, Zibin Zheng,
  Michael R. Lyu, Shing-Chi Cheung
- **Year:** 2025
- **Venue:** arXiv preprint (cs.SE)
- **DOI/URL:** arXiv:2501.10711 | https://arxiv.org/abs/2501.10711

## Questions informed
- **L1.A9.1** Agent/code-eval reproducibility pitfalls (PRIMARY -- the quantitative evidence).
- **L1.A9.2** Statistical-rigor failure rates (supports the repeat-trial / variance argument).

## GRADE tier: Moderate
arXiv preprint (DEPTH-RUBRIC §2 -> Moderate by default). Up-rate considerations: very large,
systematic sample (the title states 572 benchmarks; the methodology surveys a decade), explicit
methodology, and findings consistent with the independent Mohammadi survey (source 01) and Dror
(source 03). The specific percentages below were extracted from the arXiv HTML and are the
load-bearing quantitative claims; per DEPTH-RUBRIC §3.5 these are QA-must-verify numbers.

## Key claims (EXACT percentages, with the surrounding statement)

NOTE ON SCOPE: The title states 572 benchmarks; the percentage findings in the analyzed HTML
section are reported over the subset that was deep-inspected (the text references ~274 benchmarks
in the rigor analysis). The percentages are reproduced verbatim; AutoFirm should cite them as
"of the analyzed code benchmarks" and re-verify the exact denominator against the published
camera-ready before treating any single number as safety-critical.

- "Almost 70% of the benchmarks did not take any measures for data quality assurance."
- "Over 90% did not consider code coverage when use passing test cases as an oracle."
- "62% of benchmarks did not deduplicate or did not mention."
- "Near 80% benchmarks did not consider or handle data contamination threats."
- "Only 8.7% of benchmarks have considered test coverage when using test cases as oracles."
- "Only 35.4% of benchmark evaluations have been repeated."  <-- repeat-trial rate
- "Only 3.6% benchmarks provided their experiment environment."
- "52.6% of the benchmarks" lack disclosed prompts.
- "Only 16.7% of the benchmarks make their logged experimental results publicly available."
- "Over 34% of the benchmarks were evaluated on fewer than 3 LLMs."
- "73.3% representative benchmarks do not validate whether the prompts they used are well-designed."
- "Over 10% are not open source or only partially open source."

## HOW2BENCH checklist (the prescriptive output)
55 criteria across a 5-phase lifecycle:
- Phase 0 Design: 4 criteria
- Phase 1 Construction: 19 criteria
- Phase 2 Evaluation: 12 criteria
- Phase 3 Analysis: 10 criteria
- Phase 4 Release: 10 criteria

## Pitfall taxonomy
1. Construction -- duplicated samples, inadequate cleaning, missing validation.
2. Reliability -- insufficient test coverage, weak quality assurance (coverage-as-oracle without
   asserting consequences).
3. Reproducibility -- undisclosed prompts, missing environment details, limited repeated trials.
4. Transparency -- closed/partial open-sourcing, unremoved sensitive information.

A human study (developer survey) "revealed significant gaps in awareness" of data-quality and
reproducibility importance.

## Reproducibility note
Percentages extracted from the arXiv HTML (v1). Each is a direct quote. The exact denominator
(572 vs analyzed subset) must be re-confirmed against the camera-ready before any number is used
as a safety-critical claim (flagged for QA per DEPTH-RUBRIC §3.5).
