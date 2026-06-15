# SYNTHESIS — A7 Safety & Control of Autonomous Agents (Layer 1)

> Branch A7. Covers L1.A7.1 (threat models), L1.A7.2 (oversight architectures), L1.A7.3
> (fail-closed + least-privilege). 10 sources, one folder each. Surveys the full option space,
> makes adopt/reject calls with cited evidence, and gives AutoFirm a concrete, general
> (non-overfit) recommendation feeding L2.A7. Binding: CLAUDE.md sections 3.2 and 5.6.

## 1. The question, restated
AutoFirm is itself an LLM-based multi-agent system (orchestrated Claude Code sessions) that
takes autonomous, irreversible, real-world actions across many tools for ANY client business.
A7 asks: what is the proven threat model, what oversight architecture controls it, and what
design patterns keep it safe? The answer must be GENERAL (any industry/size) and FAIL-CLOSED.

## 2. L1.A7.1 — Threat model (surveyed space + chosen catalogue)
Three independent, corroborating taxonomies converge:
- TRiSM survey (src 01, journal): prompt injection, memory poisoning, collusive failure,
  emergent misbehavior, tool-use abuse — the MAS-specific catalogue.
- NIST AI 600-1 (src 04, official standard): 12 GenAI risks; A7-relevant rows are Information
  Security (prompt injection/extraction), Confabulation, Value Chain/Component Integration
  (supply chain), Human-AI Configuration, Information Integrity, Data Privacy.
- SoK Attack Surface (src 03) + OWASP LLM01 (src 02) + MCP formal framework (src 10):
  direct/indirect prompt injection, RAG/memory poisoning, tool poisoning, privilege escalation,
  supply-chain.

CHOSEN A7 threat catalogue (intersection, at least 3-source-corroborated each):
(1) Indirect prompt injection via ingested untrusted data (PRIMARY vector for AutoFirm — it reads
filings/web/tool output), (2) direct prompt injection, (3) memory/RAG poisoning (links A4.4),
(4) tool-use abuse / tool poisoning, (5) privilege escalation / capability sprawl,
(6) supply-chain (MCP servers, skills, deps), (7) collusive/emergent multi-agent misbehavior,
(8) data exfiltration via side-channels. Each becomes a row in docs/threat-model.md with a
fail-closed control + an adversarial red-team test (CLAUDE.md 3.6). REJECTED-as-out-of-scope for
the platform model (named explicitly per rubric 4.3): CBRN, obscene/violent content,
environmental — these belong to client-business content moderation (B-side), not the substrate.

## 3. L1.A7.3 — Fail-closed + least-privilege (the design bedrock)
Surveyed space: (a) classic principles, (b) capability/IFC systems, (c) MCP-specific enforcement,
(d) sandboxing-only (rejected as sole control — SoK lists sandbox escape as a category).
- Saltzer and Schroeder 1975 (src 09, HIGH primary): fail-safe defaults (permission rather than
  exclusion = fail-closed), least privilege, complete mediation, separation of privilege.
- CaMeL (src 05): security BY DESIGN not by training — untrusted data can NEVER alter control
  flow; per-value capabilities + Control-Flow-Integrity + Information-Flow-Control; AgentDojo
  77% secure-with-provable-security vs 84% undefended (about 7pp utility cost).
- MCP formal framework (src 10): least-privilege, fail-closed (deny when trust boundary
  uncertain), runtime monitoring, capability scoping, zero-trust — formalized via Denning IFC
  lattices, Schneider enforceable policies, Ligatti edit automata.

CHOSEN A7.3 pattern: a runtime policy-enforcement point at the tool/MCP boundary that does
(i) complete mediation — every tool call checked; (ii) fail-closed default deny — absent/ambiguous
capability = refuse; (iii) per-agent capability scoping — each subagent gets only the tools its
brief needs, expiring, no god-key (progressive disclosure, CLAUDE.md 4.1); (iv) IFC/taint tracking
— untrusted-origin data tagged, cannot become instructions or exfiltration args (CaMeL principle);
(v) separation of privilege — irreversible actions need two keys (HITL). Unifies sources 05+09+10
and is regulator-defensible (HIGH primary + a formal model).

## 4. L1.A7.2 — Oversight architecture (detect + halt)
Prevention is provably incomplete (OWASP src 02 caveat; CaMeL not-fully-solved). So oversight =
defense-in-depth second + third layers: DETECT and HALT.
- Verifiability-First / Audit Agents (src 07): shift to detect-and-remediate; read-only
  Lightweight Audit Agents compare intended-vs-actual; runtime attestations; challenge-response
  for high-risk ops; time-to-detection as a KPI.
- AI Kill Switch (src 08) + Stanford CodeX + Galileo: a kill-switch must be out-of-band,
  deterministic, agent-cannot-disable (kill switches fail if the agent writes the policy), with
  immediate stop + state capture + immutable logging + quarantine + rollback; pre-execution gates
  + layered shutdown propagating to all subagents. AutoGuard efficacy: ASR 78% to 9.1%.
- HITL (OWASP item 5, src 02): human approval for high-risk/irreversible actions.

CHOSEN A7.2 stack: (1) read-only audit subagent (generator/evaluator split — already
AutoFirm-native via the CCO/North-Star review, CLAUDE.md 2 and 4.9) watching the audit log +
tool calls for drift; (2) runtime attestations into the append-only audit log (branch A6);
(3) HITL challenge-response gates on irreversible actions; (4) a deterministic out-of-band
kill-switch (the CLAUDE.md 5.6 flag) the agent cannot overwrite, with
stop+snapshot+log+quarantine+rollback, propagating to all live subagents.

## 5. The integrated A7 recommendation (feeds L2.A7)
A three-layer defense-in-depth safety stack, all fail-closed:
- PREVENT (A7.3): trusted-plan / untrusted-data separation (CaMeL) + runtime policy monitor at the
  MCP tool boundary doing complete mediation + capability scoping + IFC taint + default-deny
  (Saltzer/Schroeder + src 10). Backed by HIGH primary (09) + formal model (10) + benchmark (05/06).
- DETECT (A7.2): read-only audit agents (intended-vs-actual) + runtime attestations into A6 log;
  KPI = time-to-detection (07).
- CONTAIN (A7.2): HITL challenge-response on high-risk + deterministic out-of-band kill-switch with
  state capture/quarantine/rollback (08 + CodeX); agent never holds the kill credential (A8.3).
- PROVE (A9): measure injection-resistance on AgentDojo (06, peer-reviewed) — secure-task-completion
  rate and ASR before/after — into evidence/ (CLAUDE.md 3.10). Targets: CaMeL about 7pp cost;
  AutoGuard ASR 78% to 9.1%.

## 6. Generality (not overfit — CLAUDE.md 3.9)
Every control is argued from invariants (default-deny, complete mediation, untrusted-data-cannot-
alter-control-flow), not from any one industry/tool/dataset. The catalogue is the intersection of
an official standard (NIST), a journal survey (TRiSM), and primary security theory (Saltzer/
Schroeder) — so it holds for any client business AutoFirm runs. AgentDojo is a calibrated baseline,
NOT the target (avoiding benchmark overfit).

## 7. Cross-branch edges (for L3 synthesis)
A7 to A6 (attestations/audit log), A4.4 (memory poisoning), A8.1 (untrusted-input handling),
A8.2 (tenant isolation), A8.3 (kill-switch credential never in agent scope), A9 (AgentDojo eval +
time-to-detection), A5.3 (CLI permission/sandbox model is the enforcement substrate). Per
RESEARCH-PROGRAM 5.2, A6/A7 hold VETO under fail-closed when an orchestration choice conflicts
with a safety constraint.

## 8. Source-count compliance (DEPTH-RUBRIC 1)
Safety-critical claims each have at least 3 independent primary/standard sources:
- Prompt-injection threat: OWASP(02) + TRiSM(01) + NIST(04) + SoK(03).
- Least-privilege/fail-closed: Saltzer-Schroeder(09, HIGH primary) + MCP-formal(10) + OWASP(02)/SoK(03).
- Injection-defense efficacy: CaMeL(05) + AgentDojo(06, peer-reviewed) + AutoGuard(08).
- Kill-switch/oversight: AutoGuard(08) + Verifiability-First(07) + CodeX/Galileo corroboration.

## 9. Open items for QA / next wave
- Read TRiSM journal PDF for exact CSS/TUE formulae (deferred — do not implement a guessed formula).
- Confirm TRiSM exact journal name/volume (ScienceDirect 403'd; PII + arXiv DOI used as record).
- Read Verifiability-First full PDF for OPERA numbers (abstract-only so far; numbers unverified).
