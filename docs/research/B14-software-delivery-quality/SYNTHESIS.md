# SYNTHESIS — B14: Software delivery & engineering quality for client products

Covers L1.B14.1 (CI/CD), L1.B14.2 (testing strategy: property/fuzz/mutation), L1.B14.3 (code-org + secure-SDLC). All claims trace to the 12 source folders here; every safety/correctness-critical or quantitative claim is corroborated by >= the DEPTH-RUBRIC source minimum.

## 1. The surveyed alternative space (and verdicts)

### Test-strategy options (B14.2)
| Option | Verdict | Why (cited) |
|---|---|---|
| Example-based unit tests only | REJECT as sufficient | ~50x weaker than PBT per test (04); coverage they produce is a weak quality proxy (02). |
| Line/branch coverage as quality gate | ADOPT as gate, REJECT as quality claim | Not strongly correlated with effectiveness once size is controlled (02); coverage < mutation for predicting real-fault detection (01). |
| Property-based testing | ADOPT (mandatory for parsers/validators/classifiers/engines) | Foundational method (03); ~50x mutation-kill vs unit tests, exception/membership/type properties ~19x best (04). |
| Coverage-guided fuzzing | ADOPT at every external-input boundary | 23,907 bugs/316 projects, 52% availability + memory-safety classes (05). |
| Mutation testing | ADOPT as the acceptance signal | 73% of 357 real faults coupled to mutants; mutation correlates with real-fault detection more than coverage (01). |
| Mutation tooling | ADOPT PIT/Stryker/mutmut/Infection, incremental | Production-used tools; cost is the blocker, solved by incremental runs (12). |

**Chosen layered strategy:** example tests (baseline) + PBT (mandatory, high-yield patterns first) + coverage gate (necessary-not-sufficient) + fuzzing (untrusted boundaries) + **mutation score as the acceptance signal**, run incrementally per PR and fully at release gates. Efficacy tests prove the product is good, not just bug-free (CLAUDE.md §3.6).

### CI/CD options (B14.1)
| Option | Verdict | Why (cited) |
|---|---|---|
| Trunk-based dev + short-lived branches + clean main | ADOPT | DORA: predictor of high performance; <3 active branches, <1-day life, no code freeze (06). Matches CLAUDE.md §4.4. |
| Long-lived feature/release branches (GitFlow) | REJECT (except mandated) | DORA ties to lower delivery performance (06). |
| Four-Keys delivery telemetry | ADOPT as client KPIs | DF, Lead Time, CFR, MTTR; throughput+stability co-move; CFR band 0-15% (06). |
| CD capability set (CI, test/deploy automation, version-control-all, shift-left security, loose coupling) | ADOPT as pipeline contract | Empirically the levers (06). |

### Code-org + secure-SDLC options (B14.3)
| Option | Verdict | Why (cited) |
|---|---|---|
| File-size limit (<=300 LOC) | ADOPT (CLAUDE.md §5.7) + add complexity signal | Maintainability/single-responsibility. |
| Cyclomatic complexity v(G)=E-N+2P gate | ADOPT as advisory trigger + test-budget sizer | Primary metric (09); but tracks size and is context-dependent - never a sole oracle. |
| Bounded review chunks (<=400 LOC) | ADOPT for the evaluator agent | Detection collapses beyond 400 LOC (10). |
| NIST SSDF (PO/PS/PW/RV) | ADOPT as secure-SDLC backbone | Government-grade outcome framework; PW mandates review+SAST+DAST+fuzz; PS provenance/SBOM (07). |
| OWASP SAMM + DSOMM | ADOPT for risk-tiering + pipeline activity checklist | SAMM 5 functions/15 practices/3 levels; DSOMM concrete pipeline activities (08). |
| Single SAST tool as security assurance | REJECT | FP 3-48%, FN 47-80% single / 30-69% combined; can have 0 true-positive rate (11). |
| Defense-in-depth (SAST+DAST+SCA+secrets+fuzz+PBT+review), fail-closed | ADOPT | Only layering reduces FN materially (11); SSDF/SAMM concur (07/08). |

## 2. The AutoFirm client software-delivery engine (recommendation for L2.B14)

A per-client, risk-tiered CI/CD pipeline with these gate contracts, all fail-closed (CLAUDE.md §5.6) and feeding `evidence/`:

1. **code-org gate** — file <=300 LOC; per-function v(G) advisory (~10); self-documenting-name lint; v(G) seeds minimum test/property count. (09, CLAUDE.md §5.7)
2. **test gate** — example + PBT (exception/membership/type patterns first) + fuzz at input boundaries; coverage threshold as necessary-not-sufficient. (02,03,04,05)
3. **mutation gate (acceptance signal)** — language tool (PIT/Stryker/mutmut/Infection), incremental per PR + full at release; covered-survivors==0 on critical modules; survivors auto-spawn harder-test tasks. (01,12)
4. **security gate** — multi-scanner SAST+DAST+SCA+secrets+fuzz, triaged/deduped, fail-closed on confirmed high/critical; technique list recorded. (07,08,11)
5. **review gate** — independent evaluator agent in <=400-LOC chunks; zero-findings-on-big-new-code triggers a deeper pass. (10, CLAUDE.md §3.7/§4.9)
6. **delivery layer** — trunk-based branching (branch-age alarm >1 day), CI + automated deploy/rollback + preview envs, Four-Keys telemetry (CFR 0-15% target). (06)
7. **provenance/release** — SBOM + signed artifacts + SSDF task-ID manifest, archived. (07; ties to A6 audit/provenance)
8. **risk-tiering** — client risk class -> DSOMM activity set + target SAMM maturity, so security is right-sized per industry (generality, CLAUDE.md §3.9). (08)

## 3. Generality & build-relevance
Every recommendation is industry-agnostic: the Four Keys, SSDF, SAMM risk-tiering, and the test-layer stack apply to any client product (B2B SaaS to fintech to manufacturing). Security effort scales by risk tier, not by industry assumption. Each gate emits machine-readable results into `evidence/` for the peer-reviewed-standard showcase (CLAUDE.md §3.10): mutation-score charts, Four-Keys dashboard, security-technique-coverage matrix.

## 4. Open items / dependencies
- OSS-Fuzz exact memory-safety % and median time-to-fix (05) not re-verified this pass — flagged, not relied upon.
- Confirm exact author list of the OOPSLA 2025 PBT paper (04) from the ACM DL record before external citation.
- L2.B14 depends on PASSED L1.A9.3 (mutation/test-adequacy, platform side) and L1.A7.* (fail-closed) — coordinate at the dependency gate.
- v(G) threshold (09) and review chunk size (10) are heuristics — make configurable, validate per language on a golden set.
