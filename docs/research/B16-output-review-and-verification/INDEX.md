# B16 — Output Review & Verification (the independent human-facing review gate) — INDEX

Branch covering the **EVALUATOR / VERIFICATION / RELEASE-GATE** method space for the
`feature/human-output-review-gate` lane. B15 covers artifact **generation**; B16 covers the
**independent review that must catch every error before any artifact reaches a human**.
Status: **GREEN — method space comprehensively surveyed across five families from primary /
peer-reviewed / professional sources.**

Research question (gates the plan at `docs/architecture/human-output-review-gate-plan.md`):
*What is the full method space for verifying a generated artifact, and which methods earn their
place in a fail-closed, institution-grade review gate — and where (if anywhere) does a model-based
reviewer layer justify itself by evidence rather than taste?*

| # | Source folder | Source (primary) | Tier | Family |
|---|---|---|---|---|
| 01 | `01-panko-what-we-know-spreadsheet-errors/` | Panko, *What We Know About Spreadsheet Errors* (1998; rev. EuSpRIG, arXiv:0802.3457) | High (peer-reviewed survey) | Why self-review fails; detection rates |
| 02 | `02-aurigemma-panko-human-vs-inspection-software/` | Aurigemma & Panko, *The Detection of Human Spreadsheet Errors by Humans versus Inspection (Auditing) Software* (2010, EuSpRIG, arXiv:1009.2785) | High (peer-reviewed experiment) | Automated vs human audit efficacy |
| 03 | `03-panko-halverson-error-taxonomy/` | *Revisiting the Panko-Halverson Taxonomy of Spreadsheet Errors* (2008, EuSpRIG, arXiv:0809.3613) | High (peer-reviewed) | Defect taxonomy the gate must cover |
| 04 | `04-zheng-llm-as-a-judge-mtbench/` | Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* (2023, NeurIPS; arXiv:2306.05685) | High (peer-reviewed, foundational) | LLM-as-judge: agreement + biases |
| 05 | `05-verga-replacing-judges-with-juries/` | Verga et al., *Replacing Judges with Juries: Evaluating LLM Generations with a Panel of Diverse Models (PoLL)* (2024, arXiv:2404.18796) | High (peer-reviewed) | Jury/ensemble; bias + cost mitigation |
| 06 | `06-wu-self-preference-bias/` | *Self-Preference Bias in LLM-as-a-Judge* (2024, arXiv:2410.21819) | Moderate–High | Self-preference bias, quantified |
| 07 | `07-no-free-labels-human-grounding/` | *No Free Labels: Limitations of LLM-as-a-Judge Without Human Grounding* (2025, arXiv:2503.05061) | Moderate–High | When LLM judges are NOT trustworthy |
| 08 | `08-landis-koch-cohens-kappa/` | Landis & Koch, *The Measurement of Observer Agreement for Categorical Data* (1977, *Biometrics* 33:159–174); Cohen (1960) | High (foundational statistics) | Inter-rater reliability metric for the gate |
| 09 | `09-boehm-ivv-and-defect-economics/` | Boehm & Basili, *Software Defect Reduction Top 10 List* (2001, IEEE Computer); IV&V practice (HHS EPLC guide) | High (primary + professional) | Independent V&V; cost-of-escaped-defect |
| 10 | `10-icaew-how-to-review-a-spreadsheet/` | ICAEW, *How to Review a Spreadsheet* + *Twenty Principles for Good Spreadsheet Practice* (2024) | High (primary professional std) | Professional model-audit protocol |
| 11 | `11-ibcs-success-checkable-rubric/` | IBCS Association (Hichert & Faisst), *IBCS Standards v1.2* — SUCCESS / CHECK / 98 rules | High (primary std) | Objective, checkable deck/report rubric |
| 12 | `12-quality-gate-fail-closed-escape-rate/` | Software quality-gate practice — escape-rate / fail-closed gating (SonarQube quality gates; escape-rate benchmarks) | Moderate (professional) | Release-gate metrics + fail-closed design |

Synthesis: `SYNTHESIS.md` — ties the surveyed space to the gate design (deterministic floor;
whether/when a model-reviewer layer is justified; the metrics that prove the gate works).

## Alternative method space surveyed (coverage map — ADOPT / REJECT)
- **Why independent review at all:** self-review catches only ~half of errors (01, 02, 10) →
  **ADOPT generator/evaluator split as non-negotiable** (already in the plan; now independently
  grounded beyond B15's single Panko cite).
- **Deterministic / mechanical verification:** inspection software, recomputation, identity checks,
  taxonomy-driven lint (02, 03, 10) → **ADOPT as the mandatory floor.**
- **Model-based review (LLM-as-judge):** single judge (04), jury/PoLL (05) → **ADOPT only as an
  add-only ADVISORY layer, evidence-gated**, because of measured biases (04, 06) and a hard
  trustworthiness cliff on items the judge can't itself solve (07).
- **Reject-as-sole:** any LLM-judge-as-acceptance-authority (07 shows κ collapse 0.78→0.14);
  self-assessment by the builder (01); coverage/pass-rate as proof of quality (12).
- **Agreement metric:** Cohen's/Fleiss' κ with Landis–Koch bands (08) → **ADOPT as the headline
  evidence metric** (gate-vs-gold-reviewer κ), alongside defect-detection rate and false-pass rate.
- **Release-gate design:** fail-closed quality gate + escape-rate (09, 12) → **ADOPT** (the plan's
  `ReleaseDecision` fail-closed authority is the right shape).

## Notes on source extraction
arXiv PDFs 01/02/03 returned compressed binary to the fetch tool; their exact statistics were taken
from the authors' published abstracts/HTML and Panko's canonical SSR write-up and are cited as such.
Where an exact figure could not be machine-verified verbatim it is flagged in the source note rather
than fabricated (per CLAUDE §3.3 — never misrepresent).
