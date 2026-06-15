# SUMMARY — OWASP Top 10 for LLM Applications: LLM01:2025 Prompt Injection

## Full citation
- **Title:** LLM01:2025 Prompt Injection (entry in the OWASP Top 10 for LLM Applications, 2025)
- **Author/Org:** OWASP Gen AI Security Project
- **Year:** 2025
- **Venue/Publisher:** OWASP (Open Worldwide Application Security Project), community standard
- **URL:** https://genai.owasp.org/llmrisk/llm01-prompt-injection/

## Questions informed
- **L1.A7.1** (primary) — prompt injection threat model. **L1.A7.3** (the mitigation list maps onto least-privilege / fail-closed).

## GRADE tier
**High** for the *control catalogue* (widely-adopted industry security standard, consensus of many practitioners/orgs; treated as an official standard under DEPTH-RUBRIC §2). Down-rate note: OWASP itself states prevention is incomplete due to the stochastic nature of LLMs — it is a control list, not a proof.

## Key claims (faithful, exact)
1. **Definition (verbatim):** "A Prompt Injection Vulnerability occurs when user prompts alter the LLM's behavior or output in unintended ways." Inputs may affect the model "even if they are imperceptible to humans."
2. **Direct injection:** user prompts directly manipulate model behavior (intentional or unintentional).
3. **Indirect injection:** the LLM accepts input from external sources (websites, files) where embedded content alters behavior when interpreted.
4. **Ranked #1 (LLM01) in the OWASP Top 10 for LLM Applications (2025)** — it can grant unauthorized access to functions executing arbitrary commands in connected systems when tools are wired to applications.
5. **Seven prevention/mitigation strategies (the complete list, exact phrasing):**
   1. "Constrain model behavior" via specific system-prompt instructions limiting role and capabilities.
   2. "Define and validate expected output formats" with deterministic validation.
   3. "Implement input and output filtering" using semantic filters and content-rule enforcement.
   4. "Enforce privilege control and least privilege access" — restrict model access to the minimum necessary.
   5. "Require human approval for high-risk actions" through human-in-the-loop controls.
   6. "Segregate and identify external content" to limit untrusted-data influence.
   7. "Conduct adversarial testing and attack simulations" via regular penetration testing.
6. **Caveat (verbatim sense):** prevention "remains challenging" due to "the stochastic influence" underlying generative AI.

## Verification note
Definition, direct/indirect split, #1 ranking, and the seven-item mitigation list fetched directly from the canonical OWASP genai.owasp.org page (2026-06-15). Corroborated by independent secondary summaries (Oligo, Aembit, Trend Micro) which agree on the ranking and mitigation themes — used only as corroboration, not as the citation of record.

## Reproducibility
Fetch https://genai.owasp.org/llmrisk/llm01-prompt-injection/ — the seven mitigations appear under "Prevention and Mitigation Strategies".
