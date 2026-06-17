# 06 — Supply-chain security of dynamically-loaded agent skills/tools

> Workstream B4. The threat case. This is *why* W4 dynamic capability loading must
> be **signed, verified, capability-declared, and fail-closed** — not load-on-trust.
> 2026 primary literature documents real, large-scale supply-chain compromises of
> agent-skill ecosystems and prompt-injection-via-skill, and prescribes concrete
> defenses W4 adopts wholesale.

## Full citation

- **Z. Li, J. Wu, X. Ling, X. Cui, T. Luo, "Towards Secure Agent Skills:
  Architecture, Threat Taxonomy, and Security Analysis"**, **arXiv:2604.02837v1**,
  Apr 2026. <https://arxiv.org/html/2604.02837v1>
- **V. P. Bhardwaj, "Formal Analysis and Supply Chain Security for Agentic AI
  Skills" (SkillFortify)**, **arXiv:2603.00195v1**, Feb 2026.
  <https://arxiv.org/html/2603.00195v1>
- **"SKILL-INJECT: Measuring Agent Vulnerability to Skill File Attacks"**,
  **arXiv:2602.20156**, Feb 2026. <https://arxiv.org/pdf/2602.20156>
- **"Supply-Chain Poisoning Attacks Against LLM Coding Agent Skill Ecosystems"**,
  **arXiv:2604.03081v1**, Apr 2026. <https://arxiv.org/html/2604.03081v1>
- Supporting standard: **SLSA** (Supply-chain Levels for Software Artifacts) L1–L4
  provenance model; **Sigstore** keyless signing; **CycloneDX** SBOM.

## Faithful structured summary (findings & defenses reproduced exactly)

**Real-world scale (Li et al., 2026).** The **"ClawHavoc"** incident (January 2026)
compromised *"over 1,184 Skills — approximately one in five packages"* in the
OpenClaw ecosystem, *deploying credential-stealing malware* via the ClawHub
marketplace. Across **42,447 skills** analysed, **prompt injection** was the most
prevalent vulnerability pattern.

**Threat taxonomy (Li et al.) — 7 categories across 3 layers (reproduced exactly):**
- **Layer 1 — Delivery & Trust:** Supply Chain Compromise; Consent Abuse.
- **Layer 2 — Runtime Attack:** Prompt Injection; Code Execution; Data Exfiltration.
- **Layer 3 — Persistent Impact:** Persistence; Multi-Agent Propagation.

**Prompt-injection-via-skill mechanism (verbatim spirit):** *"The absence of
structural separation between instruction directives and data enables attackers to
embed adversarial commands within SKILL.md files. Since natural-language
instructions occupy the agent's operator-level context, injected directives receive
elevated authority without verification of legitimacy against declared skill
purpose."* (This is the central reason an NL capability cannot be trusted on load.)

**Trust-model problem (SkillFortify, verbatim spirit):** *"developers install and
execute third-party skills with implicit trust and no formal analysis"* — no
signing, no review, no capability declaration required; the three dominant
ecosystems (OpenClaw, Anthropic Agent Skills, MCP) *"share the structural weakness:
absence of formal capability models constraining skill behaviour to declarations."*

**Defense matrix (Li et al., reproduced):**

| Threat | Defense |
|---|---|
| Supply Chain | Cryptographic publisher signing; mandatory marketplace review |
| Consent Abuse | **Version-bound trust hashes; delta-based re-approval triggers** |
| Prompt Injection | Structured query formats; untrusted-content sanitisation |
| Code Execution | Capability-tiered sandboxing; dependency version pinning |
| Data Exfiltration | Behavioral monitoring; **capability-based permission declarations** |
| Persistence | **Filesystem integrity checksums; read-only config mounting** |
| Multi-Agent Propagation | User-level message processing between agents |

**SkillFortify formal recommendations (reproduced):**
1. **Signed & verified skills** — cryptographic provenance attestations (Sigstore),
   mapping to **SLSA L3–L4** equivalents.
2. **Capability declaration** — manifest capability set **verified against static
   analysis**; flag discrepancies as violations.
3. **Lockfile reproducibility** — pin resolved versions with security bounds (not
   just hashes), enabling formal reconstruction.
4. **ASBoM** — CycloneDX-format bill of materials (EU AI Act Art. 17 compliance).
5. **Sandboxing** — capability-based runtime isolation; `Permits()` blocks
   unauthorised resource access.
6. **Trust decay** — unmaintained dependencies decay exponentially; periodic
   re-validation. (**Theorem 7.12 Trust Monotonicity:** positive evidence never
   *reduces* a skill's trust score — trust assessment is consistent under new info.)
- **DY-Skill attacker (Definition 3.5):** Dolev–Yao adversary with six ops —
  *intercept, inject, modify, drop, forge skills, compromise registries*; Theorem
  3.6 proves maximality (any symbolic attacker is simulable). **This is the W4
  threat model for the registry boundary.**

## Best parts to take (mapped to the W4 design)

1. **Sign every loadable capability; verify on load; fail closed.** No
   `CapabilityRegistryEvent` confers a *loadable* capability unless its descriptor
   carries a valid signature chained to the audited org event that created it.
   Verification failure ⇒ refuse to load (never degrade-open). *Maps to:* W4
   "signed/verified … fail-closed".
2. **Version-bound trust hash + delta re-approval (Consent Abuse defense).** Bind
   trust to the *exact* descriptor content hash; any change to a capability's
   declaration is a **new event requiring re-verification** — silently mutating an
   already-trusted capability is impossible (append-only + hash chain, sources
   01/02). *Maps to:* W4 audited growth.
3. **Capability declaration verified against behaviour (SkillFortify rec. 2 + 5).**
   The descriptor's declared authority is the enforced upper bound (source 05's
   `Permits()` / confinement). A capability that tries to exceed its declaration is
   a violation. *Maps to:* W4 least-privilege.
4. **DY-Skill as the registry threat model.** Test the W4 log/projection against
   *intercept/inject/modify/drop/forge/compromise-registry* — the hash chain must
   detect modify/drop/reorder; signing must defeat forge/inject. *Maps to:* W4
   generality test approach (combinatorial adversarial cases).
5. **ASBoM + provenance for the evidence showcase.** Emit a CycloneDX-style
   capability bill-of-materials and the head hash as audit artifacts. *Maps to:* W4
   evidence/showcase + regulatory defensibility.

## RED flags this source raises for W4

- **Never let a discovered/derived capability enter operator context unverified** —
  this is literally the dominant exploited vuln (prompt-injection-via-skill).
- **Single-approval persistent trust is broken** — re-verify on every content delta;
  a once-trusted capability is not forever-trusted.

## Cross-links

- **05** capability-based security — the formal model these defenses enforce.
- **02** hash-chain — provides version-bound integrity / tamper-evidence.
- Repo: `A7-safety-and-control/{02-owasp-llm01-prompt-injection,03-sok-attack-surface,06-agentdojo}`.
