# SUMMARY — OWASP LLM Prompt Injection Prevention Cheat Sheet

## Full citation
- **Title:** LLM Prompt Injection Prevention Cheat Sheet (OWASP Cheat Sheet Series).
- **Author/Org:** OWASP Foundation (Cheat Sheet Series project). Related: OWASP Top 10 for LLM Applications 2025 (LLM01: Prompt Injection).
- **Year:** 2025 (current edition).
- **Venue/Publisher:** OWASP (official community cheat sheet).
- **URL:** https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html

## Questions informed
- **L1.A8.1** Untrusted-input handling for LLM-driven integration.
- Supporting for **L1.A8.3** (least-privilege tool scoping).

## GRADE tier
**Moderate** (authoritative community standard; practitioner-oriented, not an empirical study).

## Key claims (recommended mitigations)
1. **Least privilege (exact):** "Grant minimal necessary permissions to LLM applications. Use read-only database accounts where possible. Restrict API access scopes and system privileges."
2. **Input/output filtering:** validate/sanitize user inputs before they reach the LLM; monitor outputs for injection signs (system-prompt leakage, API-key exposure).
3. **Human-in-the-loop (exact):** "Implement human oversight for high-risk operations" — approval required when requests contain sensitive keywords ("password", "api_key", "admin") or injection patterns ("ignore instructions").
4. **Segregate trusted/untrusted content:** "Use structured formats that clearly separate instructions from user data." Highlights the dual-LLM pattern: "A privileged LLM holds the tools but never reads untrusted content directly."
5. **Output encoding/sanitization:** "Filter suspicious markup in web content and documents"; HTML/Markdown sanitization for output rendering.
6. **Treat LLM output as untrusted:** "A guardrail LLM is itself an LLM and is itself susceptible to prompt injection."
7. **Limitation (exact):** "Research shows that existing defensive approaches have significant limitations against persistent attackers due to power-law scaling behavior"; "robust defense ... may require fundamental architectural innovations rather than incremental improvements."

## Up/down-rate reasoning
- Up-rated: official OWASP guidance; mitigations corroborate #03/#04 (least privilege, segregation, treat-output-as-untrusted).
- Down-rated: practitioner cheat sheet, not measured — the "power-law scaling" limitation is a paraphrase pointer; cite the underlying study (e.g., adaptive-attack papers) when relying on it quantitatively.

## Reproducibility note
All seven mitigation points are on the single cheat-sheet page; the "guardrail is itself an LLM" and "architectural innovations" statements are direct quotes verifiable there.
