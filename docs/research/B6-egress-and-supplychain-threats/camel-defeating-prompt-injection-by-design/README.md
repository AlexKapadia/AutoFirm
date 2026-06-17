# CaMeL — "Defeating Prompt Injections by Design"

## 1. Full Citation

- **Title:** Defeating Prompt Injections by Design
- **Authors:** Edoardo Debenedetti, Ilia Shumailov, Tianqi Fan, Jamie Hayes, Nicholas Carlini, Daniel Fabian, Christoph Kern, Chongyang Shi, Andreas Terzis, Florian Tramèr
- **Org:** Google DeepMind (with collaborators; © 2025 Google DeepMind)
- **Year:** 2025 (arXiv v1 24 Mar 2025; v2 24 Jun 2025)
- **arXiv:** 2503.18813 — https://arxiv.org/abs/2503.18813 (PDF: https://arxiv.org/pdf/2503.18813)
- **Code:** https://github.com/google-research/camel-prompt-injection
- **System name:** CaMeL = **CA**pabilities for **M**achin**e** **L**earning.

## 2. Faithful Structured Summary

CaMeL is a **defense by design** that "creates a protective system layer around the LLM, securing it even when underlying models are susceptible to attacks." It is an engineered refinement of the **dual-LLM pattern** (Willison, 2023 — see sibling folder) that adds **code generation** and **dynamic information-flow / taint tracking** with **capabilities**.

### The mechanism (faithful)

1. **Privileged LLM (P-LLM) plans, in code.** The P-LLM sees **only the trusted user query** and emits a structured, Python-like **program/plan** that expresses the control flow and data flow needed to satisfy the request. Crucially, the plan is fixed *before* any untrusted data is seen.
2. **Quarantined LLM (Q-LLM) parses untrusted data.** When the plan needs to interpret untrusted content (an email body, a web page, a retrieved document), a separate **Q-LLM** extracts the required *structured* values from it. The Q-LLM **has no tools** and **cannot influence control flow** — it only returns data.
3. **A custom (non-LLM) interpreter runs the plan.** A deterministic interpreter executes the P-LLM's program. Every value it handles carries **capabilities / metadata** — provenance/taint describing where the value came from (trusted query vs untrusted source) and what may be done with it.
4. **Security policies enforced at tool-call time.** When a tool (a consequential action) is invoked, the interpreter checks the capabilities of the arguments against policy. The paper's central guarantee: *"the untrusted data retrieved by the LLM can never impact the program flow"*, and CaMeL "uses a notion of a capability to prevent the exfiltration of private data over unauthorized data flows by enforcing security policies when tools are called."

### The two threats it defeats by construction
- **Control-flow hijacking** — injected instructions in untrusted data cannot redirect execution, because the control flow was committed by the P-LLM *before* untrusted data entered, and the Q-LLM cannot emit control flow.
- **Data exfiltration** — capability/taint metadata on values means a tool call that would send private data to an unauthorized sink is **refused by policy** (fail-closed).

### Why "provable" separation
Because trusted **planning** and untrusted **data parsing** live in physically separate models, and the deterministic interpreter — not the model — mediates every tool call against capabilities, the *separation property* is a structural invariant rather than a learned/best-effort behavior. The defense holds **even if the underlying models are themselves vulnerable** to injection.

### Benchmark result (faithful)
On **AgentDojo**, CaMeL solved **77% of tasks with provable security**, versus **84% for an undefended system** — i.e. a modest utility cost (~7 percentage points) for formal security on the protected tasks.

### Stated limitations (faithful)
- **The Q-LLM can still be prompt-injected.** It may return a *corrupted* extracted value (e.g. a wrong/poisoned summary). CaMeL guarantees the injection cannot seize control flow or exfiltrate, **not** that the parsed *content* is trustworthy.
- **Side channels.** Capability enforcement constrains explicit data flows; covert/side channels are a residual risk.
- **User-decision fatigue.** Policies that require per-action user confirmation can fatigue users into approving (a known coverage limit of the family).
- **Malicious content masquerading as data** within the system remains a modeling concern.

## 3. Best Parts to Take → AutoFirm controls

| CaMeL finding | AutoFirm control it grounds |
| --- | --- |
| **P-LLM plans control flow from trusted query only; untrusted data can never alter program flow** | This is the formal blueprint for AutoFirm's **single egress gateway with a dual-LLM / CaMeL capability interpreter** — the stated requirement that *"untrusted input cannot trigger consequential actions."* Adopt the P-LLM/Q-LLM split verbatim. |
| **Deterministic interpreter mediates every tool call against capabilities (model never holds the trigger)** | Directly grounds **propose-then-dispose**: the LLM *proposes* a plan; the **deterministic core disposes** by enforcing capability policy at the action boundary. Fail-closed: missing/ambiguous capability → refuse. |
| **Capabilities = provenance/taint on every value** | Grounds **taint-tagging every entry read from the shared knowledge layer** as untrusted, so a poisoned memory entry carries its taint into the interpreter and is blocked at any consequential sink — the key defense against shared-knowledge fan-out. |
| **Capability check blocks exfiltration to unauthorized sinks** | Grounds the egress gateway's allowlist-of-sinks / least-privilege egress policy. |
| **Limitation: Q-LLM output can still be corrupted** | Tells AutoFirm where the dual-LLM layer is *not* sufficient: the *content* of retrieved knowledge can be wrong. Justifies a **second line** (write-time provenance gating, content validation, and not trusting summaries for high-stakes decisions). |
| **~7pp utility cost for provable security** | Sets a realistic evidence baseline for AutoFirm's own gateway benchmarking. |
