# BEST-PARTS — Cisco/SmartBear code-review study

## ADOPT
1. **Bound review chunk size for the evaluator agent.** The 200-400-LOC finding tells AutoFirm's independent review agent (generator/evaluator split, CLAUDE.md §4.9/§3.7) to review in **<=400-LOC chunks** — beyond that, detection collapses. This also reinforces small, coherent commits (CLAUDE.md §3.13): smaller diffs are reviewed better.
2. **Review-rate and session limits map to agent batching.** Don't ask one review pass to digest an unbounded diff; split large changes into multiple scoped review tasks (the orchestrator fan-out pattern), mirroring the <=60-90-min human limit as a per-task scope cap.
3. **Defect-density baseline (~32/kLOC, range 10-130)** gives a sanity expectation: a review pass that finds *zero* issues on a large new feature is itself a smell (61% of real reviews found nothing, but large new code usually has defects) — prompts a harder second pass, consistent with §3.6 "if everything passes first try, make it harder".

## REJECT / BOUND
- **Bound:** vendor-authored, not peer-reviewed — treat the exact thresholds as heuristics, not laws. The *direction* (smaller chunks reviewed better) is robust and corroborated by inspection research.

## Concrete artifact this drives
- A review-batching policy: the evaluator agent receives diffs partitioned into <=400-LOC scoped units; a "no findings on substantial new code" result triggers a second, deeper adversarial review pass.
