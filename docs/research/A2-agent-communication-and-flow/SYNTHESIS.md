# SYNTHESIS — A2 Agent Communication & Workflow (Layer 1)

> Branch A2. Top priority: **reliable, audited inter-team comms.** Covers L1.A2.1 (protocols &
> message schemas / ACL lineage), L1.A2.2 (workflow/DAG vs emergent coordination & reliability),
> L1.A2.3 (standardization-of-outputs as coordination; org-theory <-> MAS bridge).
> 8 sources; primary anchors peer-reviewed/standard where load-bearing.

## 1. The alternative space surveyed (full menu, then judged)

**L1.A2.1 — Message protocols & schemas (ADOPT/REJECT/DEFER):**
- **FIPA-ACL** (IEEE std, source 04) — typed envelope, 22 performatives, feasibility/effect
  semantics, interaction protocols. **ADOPT** the envelope + bounded performative set + protocol
  templates; **REJECT** its heavyweight BDI modal-logic semantics.
- **KQML** (FIPA-ACL's predecessor, source 04) — **REJECT** wire format; superseded by FIPA-ACL.
- **MCP** (Anthropic, source 01) — **ADOPT** as the agent<->tool/data plane (native to the
  Claude Code substrate).
- **A2A** (Google, source 01) — **ADOPT** Agent-Card capability descriptors + JWS signing for
  the inter-agent plane.
- **ACP** (IBM, source 01) — **ADOPT** async-first + streaming + signed manifests pattern.
- **ANP** (source 01) — **DEFER** (open DID marketplace; overhead unjustified for an internal
  governed company).
- **Semantic layer** (source 03) — **ADOPT** a minimal versioned vocabulary + explicit intent
  field; **DEFER** formal OWL/RDF ontology stacks.

**L1.A2.2 — Coordination/workflow models (ADOPT/REJECT):**
- **Deterministic DAG / declared topology** (source 08) — **ADOPT as default** for structured
  flows (cheap, auditable, zero-token routing).
- **LLM-as-orchestrator / dynamic routing** (source 08) — **REJECT for structured flows**;
  reserve for exploratory work only.
- **Contract Net negotiation** (Smith 1980, source 05) — **ADOPT** for *dynamic* task allocation
  where the right agent is unknown at design time.
- **Blackboard / shared-memory** (surveyed) — **DEFER**; better decoupling but coordination-
  control overhead and conflicting-write risk; revisit for A4 shared memory, not the comms plane.
- **Pure emergent / mutual-adjustment chat** — **REJECT at scale** (MAST FC2 = 36.94%, source 02;
  Mintzberg: doesn't scale beyond adhocracy, source 06).
- **Orchestrator-worker hierarchy** (Anthropic, source 07) — **ADOPT** as the topology spine.

**L1.A2.3 — Standardization-of-outputs as coordination (org-theory <-> MAS bridge):**
- Mintzberg's 5 mechanisms (source 06) map 1:1 onto agent comms primitives. **ADOPT
  standardization of OUTPUTS (typed stage contracts) as the dominant coordinator**, contingent
  on flow type; reserve mutual adjustment for small exploratory sub-tasks under supervision.

## 2. The evidence on reliability (the heart of L1.A2.2)

Peer-reviewed MAST (source 02, NeurIPS 2025, 1600+ traces, 7 frameworks, kappa=0.88) is the
anchor: failures split **41.77% specification/design (FC1), 36.94% inter-agent misalignment
(FC2), 21.30% verification/termination (FC3)**. Two independent conclusions follow:
- (a) **Both** under-specified flows *and* emergent chatter fail — so AutoFirm needs **both**
  declared/deterministic structure (kills FC1) **and** typed, complete messages (kills FC2).
- (b) MAST's own caution: better protocols alone are "often insufficient" for FC2 — comms design
  must be paired with **hard role boundaries + supervision + verification** (links A1/A6/A7).

## 3. The recommendation for AutoFirm (cited, general)

**Inter-team comms = a typed, signed, intent-bearing message envelope flowing over a declared,
deterministic flow graph, with dynamic Contract-Net delegation only where the path is unknown,
coordinated primarily by standardization of typed stage outputs, and audited end-to-end.**

Concretely, the A2 contract is:
1. **Envelope (L1.A2.1):** FIPA-derived JSON fields {intent/performative (closed set),
   sender, receiver, content, vocabulary-version, conversation-id, in-reply-to, reply-by}
   (sources 04, 03) + **A2A-style Agent-Card capability header + JWS signature + scoped sender
   identity** (source 01). Required fields incl. the **Anthropic 4-part delegation contract**
   {objective, output-format, tools/sources, boundaries} (source 07). Missing required field ->
   **refuse (fail-closed)**.
2. **Flow model (L1.A2.2):** **deterministic, declared, inspectable DAG by default** (source 08);
   **Contract-Net announce->bid->award** for dynamic allocation (source 05); **orchestrator-
   worker** spine with store-and-reference compact results (source 07); a **separate
   verification step** (MAST FC3, source 02).
3. **Coordination mechanism (L1.A2.3):** **standardization of outputs** via typed stage contracts
   (Mintzberg, source 06) — specify WHAT, leave HOW; validate at each boundary (fail-closed).
4. **Audit (top priority):** every message signed + attributable + logged (append-only) with the
   award rationale and verification result -> directly satisfies "reliable, audited inter-team
   comms" and the explain-every-decision rule (CLAUDE S3.11, S5.6).

## 4. What this changes in the build (hand-off to Layer 2)

- **L2.A1 / L2.ORG:** implement the envelope schema + the hybrid flow engine (deterministic-DAG +
  CNP). Settle the contested routing choice on `experiment/{deterministic, llm-orchestrated,
  hybrid}` branches, golden-metric = {task success, tokens (~15x guardrail, source 07),
  auditability, MAST-FC2 rate vs 36.94% baseline}.
- **A6:** message signing + append-only log of every announce/bid/award/verify.
- **A3:** durable, resumable state at each step boundary (source 07).
- **A9 tests:** 14 MAST-derived adversarial tests (>=6 FC2 modes), each killed by
  contract+supervision; a free-text-only emergent baseline as the negative control.

## 5. Coverage / scope boundary
- **Excluded by scope:** blackboard shared-memory comms (deferred to A4 memory), open
  DID-marketplace federation (ANP, deferred), and the full FIPA SL/BDI logical semantics
  (impractical for LLM agents). Each exclusion is named with rationale above.
- **Source-count check:** the load-bearing reliability claim (L1.A2.2) rests on >=3 independent
  sources (MAST peer-reviewed [02] + Anthropic [07] + Microsoft/practitioner [08]); the schema
  claim (L1.A2.1) on FIPA std [04] + protocol survey [01] + semantic-view [03]; the
  coordination-mechanism claim (L1.A2.3) on Mintzberg primary [06] + corroborating peer-reviewed
  analysis (diva2:251645) + MAST evidence [02].

## 6. Open items for QA / next wave
- Recover exact per-mode MAST percentages from Table 3 before any number beyond the 3 category
  totals is treated as safety-critical.
- Re-extract the semantic-view dimension table (source 03) if its taxonomy is later relied upon.
- Confirm FIPA SC00029 Contract Net Interaction Protocol against Smith (1980) wording when L2
  implements the CNP templates.
