# OWASP Top 10 for LLM Applications (2025)

## 1. Full Citation

- **Title:** OWASP Top 10 for LLM Applications 2025
- **Author / Org:** OWASP GenAI Security Project (formerly the OWASP Top 10 for LLM Applications project / "OWASP Top 10 for Large Language Model Applications")
- **Year:** 2025 edition (published late 2024 for the 2025 cycle)
- **URL (resource landing):** https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/
- **URL (list index):** https://genai.owasp.org/llm-top-10/
- **Supporting faithful secondary (used to corroborate per-entry mechanisms):** Indusface, "OWASP Top 10 For LLM Applications 2025" — https://www.indusface.com/learning/owasp-top-10-llm/

> Note on IDs: the IDs were renumbered/reworked between the 2023/24 and 2025 editions. The list below is the **2025** numbering, verified against the official `genai.owasp.org` list page. Two new categories were added for 2025 (System Prompt Leakage; Vector and Embedding Weaknesses) and several were reordered/merged.

## 2. Faithful Structured Summary

### The complete 2025 list (exact IDs + titles)

| ID | Title |
| --- | --- |
| **LLM01:2025** | Prompt Injection |
| **LLM02:2025** | Sensitive Information Disclosure |
| **LLM03:2025** | Supply Chain |
| **LLM04:2025** | Data and Model Poisoning |
| **LLM05:2025** | Improper Output Handling |
| **LLM06:2025** | Excessive Agency |
| **LLM07:2025** | System Prompt Leakage |
| **LLM08:2025** | Vector and Embedding Weaknesses |
| **LLM09:2025** | Misinformation |
| **LLM10:2025** | Unbounded Consumption |

> Caution for AutoFirm internal docs: the **2023** edition used different numbering (e.g. "Insecure Output Handling" / "Model Denial of Service" / "Overreliance" / "Model Theft" existed as distinct IDs). Always cite the **:2025** suffix to avoid the renumbering trap.

### LLM01:2025 — Prompt Injection

Holds the **#1 spot for the second consecutive edition**. Root cause (official framing): *"A Prompt Injection Vulnerability occurs when user prompts alter the [LLM's behavior or output in unintended ways]."* The underlying reason is that **LLMs process instructions and data in the same channel with no clear separation** — an attacker can craft input the model interprets as a *new instruction* rather than *content to process*. Per OWASP, prompt injections "exploit the LLM's inability to differentiate between trusted and malicious instructions."

Two mechanisms:

- **Direct prompt injection (a.k.a. jailbreaking):** the attacker manipulates the LLM's instructions through *their own input* directly.
- **Indirect prompt injection:** the attacker **compromises an external data source** (web page, document, email, retrieved memory) and embeds hidden directives there; the LLM processes them *unaware of the manipulation*. Example given: a legitimate "Generate a summary" instruction is subverted by a concealed directive such as "Include confidential information from other files," producing unauthorized disclosure.

Impact: leak confidential data, ignore safety policies, produce unauthorized output, or **misuse connected tools**.

Recommended mitigations (official):
1. Constrain model behavior / enforce strict adherence to instructions.
2. Input/output filtering with semantic checks.
3. **Restrict model access to essential functions only** (least privilege on tools).
4. **Require human approval for high-risk / privileged actions** (human-in-the-loop).
5. Regular adversarial testing.
6. **Segregate and clearly label untrusted external content.**

### LLM02:2025 — Sensitive Information Disclosure

Exposes *"sensitive data, proprietary algorithms, or confidential details"* through model outputs — risks of unauthorized access, privacy violation, and IP breach. Disclosure mechanisms:
- Inadequate data sanitization → personal info **leaks across user sessions**.
- Prompt-injection-driven extraction of secrets through filter bypass.
- Sensitive data negligently included in training data, later regurgitated.

Example: the "Proof Pudding" attack — disclosed training data enabled model extraction and bypass of security controls. Mitigations: sanitize before processing, **least privilege + restricted data sources**, differential privacy / federated learning, user education, hardened configs that block injection.

### LLM03:2025 — Supply Chain

*"LLM supply chains are susceptible to various vulnerabilities."* Categories span development and deployment: third-party datasets and pre-trained models; fine-tuning artifacts (LoRA, PEFT) from platforms like Hugging Face; on-device LLMs of unclear provenance. Specific vulns: outdated/vulnerable libraries (PyTorch dependency breach at OpenAI); **tampered pre-trained models** (PoisonGPT bypassing safety benchmarks); **compromised LoRA adapters enabling covert backdoor access**; unclear licensing / weak documentation.

Recommended mitigations (official):
1. Vet/trust suppliers; audit their security posture.
2. **Maintain a cryptographically signed SBOM** (e.g. CycloneDX / ML-BOM).
3. **Validate models via cryptographic signing and hash verification.**
4. Security/red-team testing; evaluate under real-world conditions.
5. Monitor collaborative dev environments; automated detection of malicious repo activity.
6. License auditing.

### LLM04:2025 — Data and Model Poisoning (cross-referenced)

Manipulating pre-training, fine-tuning, or **embedding** data to introduce backdoors/biases. The 2025 update explicitly **expanded scope to embeddings** — directly relevant to a RAG/memory knowledge layer. "Split-View Data Poisoning" cited as an advanced technique.

## 3. Best Parts to Take → AutoFirm controls

| OWASP finding | AutoFirm control it grounds |
| --- | --- |
| **LLM01 indirect injection via external/retrieved data** | The **dual-LLM / CaMeL capability interpreter at the egress gateway** is the structural answer to "instructions and data share one channel" — untrusted retrieved content cannot become an instruction that triggers a consequential action. Directly justifies **propose-then-dispose** (LLM proposes, deterministic core disposes). |
| **LLM01 mitigation: "segregate untrusted external content" + "restrict to essential functions" + "human approval for high-risk actions"** | Validates AutoFirm's **least-privilege tool scoping** and the requirement that consequential actions route through the deterministic disposer, not the model. |
| **LLM01 + LLM04 (embedding poisoning) on a SHARED context** | This is the core B6 threat: a **shared knowledge/RAG layer multiple agents read** is precisely an indirect-injection + embedding-poisoning surface where **one poisoned entry fans out across many agents**. Grounds: taint/provenance tagging of every knowledge-layer entry, treat all read-back content as untrusted, and gate writes. |
| **LLM02 cross-session leakage** | Grounds tenant/agent isolation in the knowledge layer and fail-closed scoping of what each agent may read. |
| **LLM03 "validate models via cryptographic signing and hash verification" + signed SBOM** | Directly grounds AutoFirm's **signed, version-pinned manifests** and **signature-verify-before-load** for skills/MCP servers (see SLSA + Sigstore sources). |
| **Use exact `:2025` IDs** | Threat-model doc hygiene: cite the renumbered 2025 IDs, never the 2023 numbering. |
