# SYNTHESIS — B10: Legal, Compliance & Risk Foundations (L1.B10.1)

> Branch: **B10-legal-compliance-risk** · Question: **L1.B10.1** (entity formation, contracts, IP,
> regulatory map). Feeds **L2.B10** (legal/compliance/risk playbook), **L2.B12** (industry
> parameterization), **L2.A7** (safety), **L2.B15/B13** (artifact/design IP). 9 sources; all <300 lines.

## 1. The question, scoped
AutoFirm builds and operates **real companies of any size in any industry** via autonomous agents.
The legal/compliance/risk foundation must answer four pillars **generally** (not for one industry):
**(P1) entity formation**, **(P2) contracts**, **(P3) IP**, **(P4) the regulatory map** — PLUS the
cross-cutting frontier unique to AutoFirm: **who is legally liable when an autonomous agent acts.**

## 2. Surveyed alternative space (full menu, with adopt/reject)

### P1 — Entity formation (source 01)
Full menu surveyed: **sole proprietorship, general partnership, LP, LLP, LLC, S-corp (election),
C-corp.** Decision driven by **4 axes** (liability, taxation, capital-raising, admin burden — SBA).
- **ADOPT:** a **parameterized entity-selection decision function** over the 4 axes + industry/funding
  intent; separate `entity_type` from `tax_classification` (IRS treats them orthogonally).
- **REJECT:** hard-coding "always Delaware C-corp" or any single jurisdiction; numeric tax rates in code.

### P2 — Contracts (sources 02, 06)
Full menu surveyed: **common-law regime** (services; mirror-image rule; all-material-terms definiteness;
free revocability) vs. **UCC Article 2** (goods; §2-207 displaces mirror-image; §2-204 gap-fillers;
§2-205 firm offer up to 3 months). Plus **electronic-agent formation** (UETA §2(6)/§14, E-SIGN §7001).
- **ADOPT:** a **typed formation contract** (offer/acceptance/consideration/capacity/legal-purpose) with
  a **subject-matter regime router** (goods to UCC, services to common law), and an **authority guard**
  that records the authorizing principal + scope on every agent-formed contract.
- **REJECT:** auto-binding on ambiguous assent; letting the agent self-grant authority.

### P3 — IP (sources 03, 04, 09)
Full menu surveyed: **patent, copyright, trademark, trade secret** (+ WIPO industrial designs,
geographical indications). Mechanisms differ and some **oppose** (patent = disclose; trade secret =
never disclose). Two AutoFirm-critical edges: **trade-secret status requires "reasonable secrecy
measures"** (DTSA s.1839(3)) and **purely AI-generated works are not copyrightable in the US** (Thaler).
- **ADOPT:** an **IP register** classifying assets to protection mechanism + next action; the private/
  public workspace boundary (A6.4) as the **legal precondition** for trade-secret status; an
  **AI-authorship advisor** tagging generated artifacts with copyright-status advisories.
- **REJECT:** one-size IP strategy (patenting a secrecy-valued asset); claiming the agent as "author."

### P4 — Regulatory map (source 08)
Full menu surveyed: **EU AI Act** (4 risk tiers: prohibited/high/limited/minimal; Reg. 2024/1689) +
sector regimes — **HIPAA** (healthcare PHI), **GLBA/BSA-AML/KYC/PCI DSS** (finance), **GDPR/CCPA**
(privacy). Each fixed-panel industry maps to a distinct bundle.
- **ADOPT:** a **parameterized regulatory-profile engine** keyed on (industry, jurisdiction, data-types)
  to applicable-regime bundle + required controls; an **AI-Act tier classifier** for AutoFirm own
  agents (refuse prohibited-practice capabilities, fail-closed).
- **REJECT:** a single static compliance checklist; statutory content baked into code (must be versioned
  data).

### Cross-cutting frontier — liability attribution (sources 06, 07; capability bound by 05)
Strong **multi-source agreement** (UETA/E-SIGN + Proskauer + Squire Patton Boggs + Kolt + Jones Walker):
**AI agents are not legal persons; liability and contractual binding flow to the DEPLOYER/user** via
agency, product-liability, and negligence doctrines. LegalBench (05) shows LLM legal reasoning is
**uneven by reasoning type**, so deterministic guardrails own must-never-fail decisions; LLM is a soft
explanatory layer (CLAUDE.md §3.5 hybrid).

## 3. Concrete, cited recommendation for AutoFirm (the build implication)

**B10 yields a deterministic legal-core + soft-LLM-layer architecture** (hybrid, CLAUDE.md §3.5), with
these components for L2.B10:

1. **`entity_selection`** — 4-axis decision function; pluggable jurisdiction module (src 01).
2. **`contracting/{formation_guard, regime_router, authority_guard}`** — typed assent, goods/services
   routing, and **principal+scope on every agent-formed contract** (src 02, 06). The authority guard is
   **safety-critical**: no principal / out-of-scope / over-threshold to refuse or escalate to HITL.
3. **`ip/{ip_register, trade_secret_gate, ai_authorship_advisor}`** — trade-secret status gated on
   provable secrecy controls (ties A6.4); AI-output copyright advisories (src 03, 04, 09).
4. **`compliance/{regulatory_profile_engine, ai_act_tier_classifier}`** — parameterized regime bundles;
   refuse prohibited AI practices (src 08).
5. **`risk/{risk_register, contest_outcome}`** — 5-category legal risk register + contestability
   workflow; plus a standing **compliance-oversight agent role with veto** (src 07).

**The seven SPB controls + EU AI Act Arts. 12/14/15 map 1:1 onto AutoFirm existing safety doctrine**
(audit log A6.2, HITL §2, kill-switch §5.6, tests-with-teeth §3.6). B10 contribution is supplying the
**legal citation that makes each control mandatory, not optional** — and proving liability attaches to
the deployer, so prevention-by-control (not disclaimer) is AutoFirm posture (Jones Walker).

## 4. Generality (CLAUDE.md §3.9) — proven against the fixed industry panel
Every B10 component is **parameterized**, never industry-fitted. The compliance engine must yield the
correct regime bundle for all 8 panel rows: SaaS (light/GDPR-CCPA), prof-services (light), manufacturing
(moderate/product-safety), e-commerce (light/consumer+PCI), marketplace (moderate), **fintech
(heavy/GLBA+AML+KYC+PCI)**, **healthcare (heavy/HIPAA)**, restaurant (moderate/food-safety). Overfitting
to any single row is an instant FAIL (DEPTH-RUBRIC §5-6). Entity/contract/IP engines are likewise
jurisdiction-pluggable.

## 5. Scope boundaries & open items (what L1 deliberately excludes)
- **US-centric primary law** for P1-P3 (IRS/SBA, UCC, DTSA, Copyright Office, Thaler); **EU AI Act +
  GDPR** for P4. Non-US entity/IP/contract content is **DEFERRED to per-jurisdiction modules** — flagged,
  not silently omitted. UK CDPA s.9(3) (computer-generated works) explicitly differs from US authorship.
- **Apparent-authority doctrine** for autonomous agents is **legally unsettled** (Proskauer Part III
  pending) — mitigated by explicit published authority limits + HITL; tracked as residual risk.
- **Time-sensitive figures** (tax rates, GDPR/AI-Act fine caps) live in **versioned dated config**, never
  code; re-verify at use time.
- Specific 2023 LegalBench per-model accuracies are **dated**; re-benchmark current models before quoting.

## 6. Source inventory & grade
| # | Source | Pillar | Tier |
|---|---|---|---|
| 01 | IRS + SBA entity structures | P1 entity | High (US) |
| 02 | Contract formation (UCC 2-204/205/207 + Jenkins law review) | P2 contracts | High |
| 03 | WIPO IP four/six types (+ USPTO PTRC) | P3 IP | High |
| 04 | Defend Trade Secrets Act 2016 (18 USC 1836/1839) | P3 IP | High |
| 05 | LegalBench (Guha et al., NeurIPS 2023) | capability | High |
| 06 | Electronic agents UETA 2(6)/14, E-SIGN 7001 (+Proskauer) | P2 + liability | High |
| 07 | Agentic-AI legal risk (Squire Patton Boggs + Kolt + Jones Walker) | risk | Moderate-High |
| 08 | EU AI Act 2024/1689 + sector regulatory map | P4 regulatory | High |
| 09 | AI authorship / Thaler v. Perlmutter + Copyright Office | P3 IP | High |

## 7. Reproducibility
Every claim traces to a primary statute/report/peer-reviewed paper with section locators in the per-
source SUMMARY.md. Safety-critical claims (deployer liability; trade-secret secrecy precondition;
human-authorship rule; AI-Act prohibited tier) each carry at least 3 independent primary/professional
sources per DEPTH-RUBRIC §1. No fabricated citations: where a specific number was not directly verified
in primary text (e.g. exact LegalBench per-model accuracy), it is flagged as dated/uncited rather than
asserted.
