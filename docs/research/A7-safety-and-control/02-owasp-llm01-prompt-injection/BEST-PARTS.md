# BEST-PARTS — OWASP LLM01:2025 Prompt Injection

## ADOPT
1. **The seven mitigations as AutoFirm's prompt-injection control set** — they map cleanly onto CLAUDE.md §5.6 controls:
   - #1 constrain behavior + #6 segregate/identify external content -> **trusted/untrusted content separation** (echoed by CaMeL, source 05). *Build:* every document/tool-output an agent ingests is tagged `untrusted` and may never be treated as instructions.
   - #2 validate output formats -> **typed output contracts** (A2 message schemas); reject non-conforming output fail-closed.
   - #4 least-privilege -> **per-agent scoped credentials** (CLAUDE.md §5.6 least privilege; sources 09/10). *Build:* no shared god-key; each subagent gets only the tools its brief needs.
   - #5 human approval for high-risk actions -> **HITL gates** in the A7 safety stack (CLAUDE.md §1, §5.6 fail-closed). *Build:* irreversible/external-spend/legal actions route to a human checkpoint.
   - #7 adversarial testing -> **red-team tests at every trust boundary** (CLAUDE.md §3.6 tests-with-teeth). *Build:* an injection corpus in the test suite.
2. **Treat indirect injection as the dominant risk for AutoFirm.** AutoFirm reads real public filings, web data, and tool outputs — all untrusted external content — so indirect injection (not just direct user prompts) is the primary vector. *Build:* the kill-switch and audit log must assume *any* ingested data may be adversarial.

## REJECT / DEFER
- **Reject "mitigation = solved."** OWASP itself flags prevention as incomplete (stochastic models). AutoFirm must therefore pair these controls with **detect-and-contain** (audit agents, source 07) and **architectural** defenses that hold even if the model is fooled (CaMeL-style control/data-flow separation, source 05) — defense-in-depth, not prompt hygiene alone.
- **Defer "semantic filtering" as a primary control** — it is probabilistic and bypassable (see source 03 SoK adaptive attacks); use it as a layer, never the gate.

## Concrete build implications
- Becomes the **acceptance checklist** for AutoFirm's prompt-injection defense: a green A7 gate requires all 7 controls implemented + an adversarial injection test suite that the controls survive.
- Cross-links: #4 -> sources 09/10 (least-priv mechanism); #5 -> sources 07/08 (HITL + kill-switch); #6 -> source 05 (CaMeL data/control separation).
