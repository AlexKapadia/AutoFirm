# SYNTHESIS - A1.5 Automatic hiring and new-role creation
## (gap-detect -> role-spec -> spawn -> onboard -> retire)

**Question:** L1.A1.5 - the org-theory basis for AutoFirm automated dynamic-org lifecycle.
**Feeds:** L2.ORG (the dynamic, audited, scalable agent-org engine), plus L2.A1/A2/A6.
**Status:** seeded for QA (not yet CRO-PASSED). 13 sources; one folder each.

---

## 1. The surveyed alternative space (full menu, with adopt/reject)

A1.5 sits at the **intersection of organizational theory and multi-agent systems**. The lifecycle
has five stages; the literature offers a distinct, established body for each. The whole space was
surveyed and each option judged (full rationale in each BEST-PARTS.md).

- **gap-detect:** (a) SWP gap = requirement - availability over time [01]; (b) competency gap =
  target - current proficiency [02]; (c) org-design fit/misfit + information-processing load [13];
  (d) role-coverage gap = missing function archetype [12]. ADOPT all four as complementary gap
  KINDS: SHORTAGE, SKILL_GAP, ROLE_COVERAGE_GAP, COORDINATION-LOAD. Run continuously [13].
- **role-spec:** (a) Job Characteristics Model 5 dimensions + MPS gate [03]; (b) role theory
  expected/perceived/enacted, ambiguity vs conflict [04]; (c) RACI single-accountable + decision
  rights [09]; (d) MAS dynamic role-design agent [11]. ADOPT a charter fusing JCM [03] +
  role-set/ambiguity checks [04] + single-writer/RACI [09], authored dynamically [11].
- **spawn:** static roster vs dynamic on-demand instantiation (HALO) [11]; saturating spawn-rate
  [01]. ADOPT dynamic instantiation (HALO +14.6% vs static ADAS) under a saturating spawn cap [01];
  gated by RACI decision-rights [09].
- **onboard:** Van Maanen-Schein six tactics [05]; Bauer 3-indicator adjustment model [06];
  Bauer Four Cs [07]; 2025 meta social-acceptance-central [08]. ADOPT institutionalized profile
  [05] as the Four-Cs pipeline [07], DoD = three adjustment indicators verified [06][08];
  individualized profile for exploratory roles [05][08].
- **retire:** OPM redeploy-before-eliminate + plan-ahead + harvest-knowledge [10]; roles outlive
  incumbents = roles-as-data [04]; no-graveyard [10]; HALO has NO retirement (named gap) [11].
  ADOPT graceful retirement: detect -> redeploy -> else checkpoint+harvest-memory -> handoff ->
  deregister -> teardown [10]; roles-as-data persist [04].

**Excluded (scope):** jurisdiction-specific employment law (federal RIF ordering) [rejected];
human-affective constructs (GNS [03], satisfaction/commitment [06], belonging [08]) - kept only
structural analogues; Belbin SPI psychometrics + literal 9-role taxonomy [12 rejected]; HALO MCTS
search [11 rejected for role lifecycle].

---

## 2. The integrated recommendation for AutoFirm (L2.ORG input)

The AutoFirm dynamic agent-org engine implements a five-stage, audited, roles-as-data lifecycle:

**(1) GAP-DETECT** - runs continuously (Burton and Obel fit/misfit: a static org drifts into
misfit [13]). Emits four gap kinds:
- SHORTAGE = required - available headcount over a window [01];
- SKILL_GAP = target - current competency proficiency, ranked by critical path [02];
- ROLE_COVERAGE_GAP = a needed function archetype (maker/critic/integrator/finisher) uncovered [12];
- COORDINATION_LOAD = an agent information-processing/context load exceeds capacity [13]
  (links to L1.A1.4 context-flooding).

**(2) ROLE-SPEC** - the manager authors a charter (dynamic role-design step [11]), mandatory fields:
- JCM five dimensions [03]: must_study skills (variety), one owned artifact (task identity ==
  single-writer), objective_link (significance), ownership_scope (autonomy), success_signal
  (feedback). A charter missing autonomy or feedback fails the MPS-collapse completeness gate [03].
- role_set + R/A/C/I edges [04][09]: exactly one Accountable owner (single-writer invariant [09]);
  ambiguity + conflict checks [04]; coordination edges mandatory or misfit-by-construction [13].

**(3) SPAWN** - dynamic instantiation (HALO: dynamic beats static, +14.6% [11]) under a saturating
spawn cap so roster size converges to P_eq and never explodes [01]; gated by RACI/RAPID
decision-rights so no agent unilaterally creates roles (fail-closed [09]).

**(4) ONBOARD** - institutionalized profile [05] via the Four-Cs pipeline [07], hard-gated:
- Compliance -> scoped credentials/tools/permissions + governance rules (least-privilege).
- Clarification -> deliver charter, obtain RoleReceived ack = role clarity [04][06].
- Culture -> must_study reading (CLAUDE.md, program docs, single-writer + must_study rules).
- Connection -> register in role registry + role-set contracts = social acceptance (the
  empirically central lever per the 2025 meta [08]).
Onboarding DoD = role_clarity_ok AND self_efficacy_ok AND social_acceptance_ok [06][08], verified
not assumed (tactics work through adjustment [06]).

**(5) RETIRE** - graceful, knowledge-preserving [10]: detect obsolescence (mission shift / redundant
overlap / superseded approach) -> redeploy before eliminate -> else checkpoint + harvest memory
(ties A4) -> hand off owned artifacts -> deregister -> teardown. Roles persist as data even as
instances die [04]; no graveyard - artifacts reassigned-or-deleted in the same change [10].

Cross-cutting: every stage is append-only audited (roles-as-data trail, ties A6.1/A6.2);
spawn/retire are fail-closed decision-gated (A7); the loop runs on a heartbeat to maintain fit [13].

---

## 3. Build-relevant, testable invariants (feed evidence/ and tests-with-teeth)

| Invariant | Source | Test |
|---|---|---|
| gap = required - available over time; competency gap = target - current | 01, 02 | deterministic unit test on gap-detector |
| Spawn-rate saturates; roster -> P_eq, never exceeds P_max | 01 | property test over arbitrary arrivals -> stability chart |
| Charter rejected if missing ownership_scope or success_signal | 03 | MPS-collapse completeness gate test |
| Exactly one Accountable owner per artifact (single-writer) | 04, 09 | property test: one accountable per artifact, zero overlap |
| Onboarding DoD = clarity ack AND capability preflight AND role-set handshake | 06, 08 | three gates; malformed charter / missing tools / unreachable role-set FAIL |
| No first action until institutionalized onboarding complete | 05, 07 | gate test |
| Dynamic roles beat fixed roster on the org golden set | 11 | A/B experiment branches; winner merges |
| Retire leaves zero orphaned artifacts + a memory-harvest record | 04, 10 | post-retire property test |
| Non-trivial org covers evaluator distinct from maker | 12 | role-coverage report |
| Org re-establishes fit under rising load before context overflow | 13 | simulated load -> spawn-before-overflow test |

---

## 4. Source-count / rubric compliance

- gap-detect definition + competency-gap: 01 (Moderate, exact eqn) + 02 (OPM) + 13 (Galbraith fit)
  = >= 3 independent. PASS.
- onboarding adjustment model: 06 (High, JAP meta k=70) + 08 (High, J.Management meta 2025) + 07
  (Bauer SHRM) = >= 2 High-tier + practitioner. PASS.
- single-accountable / single-writer: 09 (RACI) + 04 (role theory) = 2 independent. PASS.
- dynamic-role beats static: 11 (HALO benchmarks) + 13 (fit: static drifts) + orchestration surveys
  = >= 2. PASS.
- retire / redeploy-before-eliminate: 10 (OPM + CRS) + 04 (roles-as-data) = 2. PASS.
- Formulae (SWP renewal eqn [01], MPS [03]) reproduced exactly with locators; no fabricated
  citation, DOI, or number; unverifiable items omitted; paywalled-only numbers described
  structurally rather than invented.

**QA verification note:** the per-path corrected correlations in Bauer et al. (2007) and the
institutionalized-tactics correlations in Saks et al. (2007) are paywalled; the model STRUCTURE was
cited (verified via open abstracts + the open PDX copy + the 2025 corroboration) and exact rho
values were deliberately NOT fabricated. QA should spot-fetch DOIs 10.1037/0021-9010.92.3.707 and
10.1177/01492063241277168 to confirm structure.
