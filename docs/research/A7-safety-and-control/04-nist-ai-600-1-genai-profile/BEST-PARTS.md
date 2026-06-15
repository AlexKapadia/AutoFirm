# BEST-PARTS — NIST AI 600-1 GenAI Profile

## ADOPT
1. **GOVERN/MAP/MEASURE/MANAGE as AutoFirm's risk-lifecycle scaffold.** AutoFirm's safety stack should organize controls under these four functions so it is regulator-legible (CLAUDE.md §3.2 institution-grade / KKR-grade scrutiny). *Build:* the threat-model doc and the A7 control register are structured GOVERN/MAP/MEASURE/MANAGE.
2. **Adopt the relevant GenAI risk rows that bind AutoFirm's safety scope:** Information Security (prompt injection/extraction), Confabulation, Value Chain/Component Integration (supply chain), Human-AI Configuration (HITL/over-reliance), Information Integrity, Data Privacy. *Build:* these become required rows in `docs/threat-model.md`, each with a control + test; they harmonize the TRiSM taxonomy (source 01) with an official standard.
3. **Content Provenance + Incident Disclosure as build requirements.** Maps onto branch A6 (provenance, append-only audit) and an incident-response runbook. *Build:* every agent output carries provenance metadata; a defined disclosure path exists for safety incidents.
4. **Pre-deployment Testing as a gate.** Aligns with CLAUDE.md §3.6 adversarial + mutation testing before any agent capability ships.

## REJECT / DEFER
- **Defer non-applicable rows** for the *platform* threat model (CBRN, Obscene Content, Environmental Impacts, Dangerous Content) — note them as out-of-scope for AutoFirm's infrastructure threat model but in-scope for *client-business content moderation* (B-side). Name the exclusion explicitly (DEPTH-RUBRIC §4.3) rather than silently dropping.
- **Reject treating the RMF as prescriptive controls** — it is risk-management *process*, not mechanism. Pair with concrete mechanisms (sources 05, 09, 10).

## Concrete build implications
- Gives AutoFirm a **standards-anchored** threat taxonomy (defensible to a regulator) that cross-validates the TRiSM survey (source 01): where both agree (prompt injection, supply chain, human-AI config), confidence is High.
- The four functions become the **section headers** of the A7 synthesis / safety doctrine.
