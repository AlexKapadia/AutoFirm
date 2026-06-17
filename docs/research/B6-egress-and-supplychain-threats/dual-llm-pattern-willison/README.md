# The Dual LLM Pattern (Willison, 2023) — CaMeL precursor

## 1. Full Citation

- **Title:** The Dual LLM pattern for building AI assistants that can resist prompt injection
- **Author:** Simon Willison
- **Year:** 25 April 2023
- **URL:** https://simonwillison.net/2023/Apr/25/dual-llm-pattern/

This is the **precursor** that CaMeL (Debenedetti et al., 2025) explicitly refines. It is the original articulation of trusted-plan / untrusted-data separation for tool-using LLM assistants.

## 2. Faithful Structured Summary

### Core components
- **Privileged LLM (P-LLM):** accepts input **exclusively from trusted sources** (primarily the user) and has **full access to tools** and state-changing operations (send email, modify calendar). Implements the ReAct pattern.
- **Quarantined LLM (Q-LLM):** processes **untrusted content** and **deliberately has no tool access**. It is assumed it may "go rogue at any moment," since it is exposed to injection via emails, web pages, etc.

### Symbolic references + the Controller (the key idea)
Untrusted content is **never passed directly between models**. A **Controller** — *regular software, not an LLM* — mediates using **symbolic variable references** like `$VAR1`, `$VAR2`. Worked flow when the P-LLM asks to summarize an email:
1. Controller fetches the email → assigns it to `$VAR1`.
2. Controller invokes the Q-LLM with the actual content substituted ("Summarize this: <content>").
3. Q-LLM returns a result.
4. Controller stores it as `$VAR2`.
5. **The P-LLM only ever sees the variable names, never the raw or tainted content.**

> Quoted: *"The Privileged LLM only ever sees those variable names. It is never exposed to either the untrusted content from the email, or the tainted summary."*

### Stated limitations (faithful)
- **Social engineering:** *"Tricking users into copying and pasting out obfuscated data could still be effective even if they can't click directly on links or load data leaking images."*
- **Chaining risk:** piping Q-LLM output into further prompts is dangerous — *"a sufficiently devious malicious prompt could cause that LLM's output to carry the same or a modified version of the intended prompt injection attack."*
- **Complexity / UX cost:** Willison concedes the approach is *"pretty bad"* and will *"likely result in a great deal more implementation complexity and a degraded user experience."* (CaMeL's contribution is making this tractable via code generation + capability tracking.)

## 3. Best Parts to Take → AutoFirm controls

| Dual-LLM finding | AutoFirm control it grounds |
| --- | --- |
| **Controller is plain software, not an LLM; it substitutes content the P-LLM never sees** | Grounds the **deterministic core** in propose-then-dispose: a non-LLM controller mediates between the planning model and untrusted data. The trigger for consequential actions lives in deterministic code, not the model. |
| **Q-LLM has no tools; P-LLM never sees untrusted content** | The minimal viable shape of AutoFirm's egress gateway dual-LLM split, before CaMeL's capabilities are added. |
| **Symbolic `$VARn` references = taint isolation by indirection** | Conceptual basis for tagging/holding shared-knowledge content by reference so untrusted strings never reach the privileged planner verbatim. |
| **Limitation: chaining can re-carry the injection** | Warns AutoFirm that **agent-to-agent relay through the shared knowledge layer** can propagate an injection — reinforces taint must travel *with* the value across agents, not be dropped at a hop. |
