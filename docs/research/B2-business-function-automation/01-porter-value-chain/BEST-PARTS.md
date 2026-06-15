# BEST-PARTS — Porter's Value Chain → AutoFirm

## ADOPT
- **The 9-activity generic value chain as AutoFirm's TOP-LEVEL function spine (L2.B2).** Every
  company AutoFirm builds is decomposed first into Porter's 5 primary + 4 support activities. This
  is industry-agnostic by construction (Porter intended it for any firm), satisfying the
  generality bar (CLAUDE §3.9). **Build implication:** the L2.B2 function-decomposition engine
  emits a typed `ValueChainActivity` enum with exactly these 9 members; each agent-org sub-team
  (B5–B11 playbooks) attaches to one or more activities (Marketing&Sales→B7/B8; Service→B9;
  Firm infrastructure→B6/B10; Operations/Inbound/Outbound→B11; Procurement→B11; Technology dev→B14).
- **Direct / indirect / QA sub-distinction** maps cleanly onto AutoFirm's own org doctrine:
  *direct* = value-producing agents, *indirect* = orchestration/scheduling, *QA* = the
  North Star/CCO + Peer-Review functions. Reuse the distinction to classify which agent roles are
  billable-value vs. coordination overhead.
- **Linkages / value-system concept** → the typed data contracts between pipeline stages
  (CLAUDE §1 CTO). A linkage is exactly a contract between two activities; optimizing linkages =
  minimizing coordination cost (ties to A1.4 context-flooding theory).

## REJECT / use-with-care
- **Reject Porter as the *operational* (lowest) taxonomy level.** It is a *strategic* abstraction;
  9 buckets are too coarse to drive task-level automation decisions. AutoFirm must nest a
  finer process taxonomy underneath it (see source 03 APQC PCF) — Porter is the L1 spine, APQC is
  the L2–L4 detail.
- **Reject the implicit linear, manufacturing-first flow** (inbound→ops→outbound) as the *only*
  ordering. For digital/SaaS, marketplace, and services firms the physical-logistics activities
  collapse or invert; the decomposition engine must allow activities to be *empty or merged* per
  industry (proven against the B12 fixed panel), not force a manufacturing sequence.

## Concrete build implication
- Component: `function_decomposition/value_chain_activity_taxonomy.py` (typed 9-member enum + per-activity metadata).
- Test it drives: a generality test asserting all 8 B12 panel industries map onto the 9 activities with at least one activity legitimately empty/merged for the digital rows — proving no manufacturing overfit.
