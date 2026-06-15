# INDEX — A3: Long-Horizon Autonomy, Handoff & Resume

Branch A3 of the AutoFirm research ontology (Layer-1 Foundations). One folder per source.
Status: **seeded — not yet QA-PASSED** (awaiting independent QA + CRO sign-off per RESEARCH-PROGRAM.md §2–3).

## Questions covered
- **L1.A3.1** Levels-of-autonomy frameworks
- **L1.A3.2** Long-horizon failure modes (drift, goal misgeneralization, context loss)
- **L1.A3.3** Checkpoint / handoff / resume mechanisms & state externalization

## Sources
| # | Source (folder) | Primary question | Tier |
|---|---|---|---|
| 01 | CSA — Leveling Up Autonomy in Agentic AI (Reavis 2026) | L1.A3.1 | Low–Mod |
| 02 | Interface/Ada Lovelace — Autonomy-Based Classification (Soder et al. 2025) | L1.A3.1 | Moderate |
| 03 | Cihon et al. — Measuring AI agent autonomy via code inspection (SoLaR 2024 / 2025) | L1.A3.1 | Moderate |
| 04 | METR/Kwa et al. — Measuring AI Ability to Complete Long Software Tasks (2025) | L1.A3.1, L1.A3.2 | Mod–High |
| 05 | Wang et al. — Long-Horizon Task Mirage (COLM 2026) | L1.A3.2 | Mod–High |
| 06 | Zhu et al. — Where LLM Agents Fail / AgentDebug (2025) | L1.A3.2 | Moderate |
| 07 | Langosco et al. — Goal Misgeneralization in Deep RL (ICML 2022) | L1.A3.2 | High |
| 08 | Garcia-Molina & Salem — Sagas (SIGMOD 1987) | L1.A3.3 | High |
| 09 | Elnozahy et al. — Rollback-Recovery Survey (ACM Comput. Surv. 2002) | L1.A3.3 | High |
| 10 | Chang & Geng — SagaLLM (2025) | L1.A3.3 | Moderate |

## Source-count check (DEPTH-RUBRIC §1)
- L1.A3.1: 4 independent sources (01–04) + SAE J3016 lineage. ✔ (>= 2 for architecture-choice; convergent)
- L1.A3.2: 4 sources (04, 05, 06, 07), incl. one **High**-tier peer-reviewed (07) and two independent author groups (05, 06). ✔
- L1.A3.3: 3 sources, two **High**-tier peer-reviewed primaries (08 SIGMOD, 09 ACM CSUR) + LLM bridge (10). ✔ (meets the >=3 safety/correctness bar for the checkpoint/recovery invariants)

## See also
- `SYNTHESIS.md` — surveyed space + cited recommendation for AutoFirm (feeds L2.A3, L2.A7).
- Cross-branch: A4 (memory), A5.2 (CLI resumability/idempotency), A6 (audit log as replay log), A7 (fail-closed/HITL), §4.8 watchdog auto-resume.
