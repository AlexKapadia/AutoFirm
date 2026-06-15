# AutoFirm — Branch-Per-Experiment Specifications (Gate-2 v1, ratified)

> The evidence-driven method-selection plan (CLAUDE.md §3.4, §4.4/§4.5). Each experiment E1–E8 from
> `docs/research/_program/LAYER1-SIGNOFF.md` §5 is specified here: **hypothesis, competing approaches,
> golden set + metric (pre-agreed, up front), and the `experiment/<name>` branch to run it on.**
> Each branch is **pushed and visible**; the **evidence-backed winner merges to main and the losers
> are deleted in the same change (no graveyard).** All comparisons use the A9 statistical procedure
> (pass@k / pass^k; McNemar→Wilcoxon→bootstrap for pairs; Friedman+Nemenyi for ≥3; effect size + CI;
> repeated trials; **no averaging across industries**) and the **mutation score** is the acceptance
> signal, not pass rate (A9, B14).

---

## E1 — Orchestration topology bake-off  (L2.A1; resolves T5)
- **Branch:** `experiment/orchestration-topology`
- **Hypothesis:** an orchestrator-worker spine plus *bounded* dynamism beats both a bare spine and an
  over-dynamic mesh on task success per cost.
- **Competing approaches:** (a) orchestrator-worker spine only; (b) spine + bounded debate subroutine
  (3 agents, ≤4 rounds); (c) spine + dynamic-role-instantiation.
- **Golden set:** AutoFirm task golden set spanning decomposable + sequential + breadth-first tasks.
- **Metric:** task success × token cost; **error-amplification** (target ≤ centralized 4.4×, A1);
  **MASFT 14-mode failure incidence** (A1/A2); fan-out saturation at ~3–4 (A1).
- **Cite:** A1 (routing predicate, saturation, MAST), A2 (deterministic-DAG default).

## E2 — Dynamic-vs-static org engine  (L2.ORG; gates T4)
- **Branch:** `experiment/dynamic-org-engine`
- **Hypothesis:** the A1.5 dynamic roles-as-data org outperforms a fixed roster on AutoFirm's *own*
  org golden set.
- **Competing approaches:** (a) fixed role roster; (b) A1.5 five-stage dynamic lifecycle.
- **Golden set:** AutoFirm org golden set (multi-client, multi-function build scenarios).
- **Metric:** task success + coordination cost under **A9 Friedman+Nemenyi with CD diagram**, effect
  size + CI, repeated trials. **The HALO +14.6% external number is NOT the bar** (T4).
- **Merge gate:** also requires A1.5 CRO-PASSED (org-model §7). **Cite:** A1.5, A9.

## E3 — Memory architecture  (L2.A4)
- **Branch:** `experiment/memory-architecture`
- **Hypothesis:** a hybrid linked-notes + OS-tiering memory beats either alone on long-horizon recall
  and poisoning resistance.
- **Competing approaches:** (a) A-Mem linked-notes; (b) MemGPT OS-tiering; (c) hybrid.
- **Golden set:** long-horizon recall + poisoning-resistance suite (AgentPoison-style injection at
  <0.1% poison rate).
- **Metric:** recall@k (hybrid RAG vs BM25 baseline); **AgentPoison ASR** (defended vs undefended);
  **VF exact-deletion verification** (auditable non-recoverability); tokens-per-query vs accuracy
  (memory beats context-stuffing). **Cite:** A4 (CoALA, A-Mem, MemGPT, DPR, AgentPoison, SISA).

## E4 — Injection-defense pattern  (L2.A7 / A8)
- **Branch:** `experiment/injection-defense`
- **Hypothesis:** a capability-interpreter defense retains acceptable utility while provably blocking
  consequential actions from untrusted input.
- **Competing approaches:** (a) Plan-Then-Execute; (b) Dual-LLM (quarantined reader + privileged
  orchestrator + symbolic vars); (c) CaMeL capability interpreter.
- **Golden set:** AgentDojo (97 tasks, 629 security cases).
- **Metric:** utility retained vs attack-blocked; **quantify CaMeL's utility cost** (≈77% secure vs
  84% undefended baseline); secure-task-completion before/after. **Cite:** A7, A8.1 (CaMeL, AgentDojo).

## E5 — Tamper-evident log mechanism  (L2.A6)
- **Branch:** `experiment/tamper-evident-log`
- **Hypothesis:** a Merkle/history-tree log gives O(log n) proofs and complete tamper detection at
  fail-closed cost acceptable for the gate cadence.
- **Competing approaches:** (a) plain hash-chain; (b) history-tree (Crosby-Wallach); (c) RFC-6962
  Merkle / STH.
- **Golden set:** synthetic append + tamper/truncation attack suite; RFC-6962 MTH known-answer test.
- **Metric:** append latency, proof size (O(log n) vs O(n)), **tamper-detection completeness at
  fail-closed**; enforcement latency <200 ms target (A6). **Cite:** A6 (history-tree, RFC 6962, STH).

## E6 — B12 panel generalization proof  (L2.B12; discharges LAYER1-SIGNOFF Note B)
- **Branch:** `experiment/playbook-generalization`
- **Hypothesis:** `derive_playbook(profile)` yields a non-empty, lawful, domain-expert-sensible
  playbook for **every** panel row without overfitting any one.
- **Competing approaches:** the single `derive_playbook` engine run across **all 8 fixed panel rows**
  (B2B SaaS, prof. services, discrete mfg, e-commerce/DTC, two-sided marketplace, fintech/payments,
  healthcare/digital-health, restaurant/food-service).
- **Golden set:** the 8-row fixed panel (B12).
- **Metric:** every row yields a lawful (fail-closed on unlawful variants), non-empty, sensible
  variant with industry-appropriate KPIs; **overfitting to any single row = FAIL**; property/fuzz
  tests confirm no unlawful variant escapes. **Cite:** B12 (IndustryProfile/PlaybookSpine/C-EPC).

## E7 — Artifact-generation engine  (L2.B15)
- **Branch:** `experiment/artifact-generation`
- **Hypothesis:** a formula-live spreadsheet pipeline + message-driven deck router beats value-dump
  generation on integrity and error rate.
- **Competing approaches:** (a) XlsxWriter + LibreOffice-headless recalc (live formulas); (b)
  value-dump baselines (e.g. pandas.to_excel) as negative control; deck router (Minto/Zelazny/Tufte/
  IBCS) vs unstructured.
- **Golden set:** financial-model + deck + document fixtures with injected mechanical/logic/omission
  faults.
- **Metric:** **error-class kill-rate** (target ~100% on injected faults) vs **Panko ~86%** human
  baseline; transparency_score (FAST/ICAEW); accounting identities exact-to-the-cent; recalc
  determinism; IBCS SUCCESS 7-rule pass; file_opens_clean. **Cite:** B15 (FAST, ICAEW, Panko, IBCS).

## E8 — Live-E2E design DoD  (L2.B13)
- **Branch:** `experiment/live-e2e-design`
- **Hypothesis:** a role-based auto-retrying E2E harness proves "nothing static" better than
  alternatives and clears the UI Definition-of-Done.
- **Competing approaches:** (a) Playwright (role-based locators); (b) Cypress; plus a11y-scanner
  choice bake-off.
- **Golden set:** a reference UI exercising every interactive element across all four states
  (loading/empty/error/ideal+edge).
- **Metric:** **every interactive element exercised** (button/input/link/flow, happy + failure path);
  **WCAG 2.2 AA** pass (24×24px, 4.5:1/3:1, keyboard/focus, auto + manual); **Core Web Vitals**
  budget (LCP ≤ 2.5s, CLS ≤ 0.1, INP ≤ 200ms @ p75); token adherence (no hard-coded values).
  **Cite:** B13 (Nielsen, WCAG 2.2, CWV, Playwright), CLAUDE.md §4.9.7.

---

## Run discipline (binding)
- Define the golden set + metric **before** writing candidate code (A9, CLAUDE.md §4.5).
- Each candidate on its **own pushed branch**; evaluate all under identical conditions.
- **Winner merges to main; losers deleted in the same change** (no graveyard — CLAUDE.md §3.8).
- Record **why the winner won** (the numbers) in `evidence/` to peer-reviewed standard (CLAUDE.md
  §3.10): means ± CI, the A9 test used, mutation score, and the per-experiment metric above.
- **Never overfit** to the golden set; correctness argued from invariants/properties (CLAUDE.md §3.9).
