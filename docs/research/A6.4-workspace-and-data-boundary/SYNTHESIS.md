# SYNTHESIS — A6.4: Workspace Organization & the Public/Private Data Boundary

> Layer-1 foundations for AutoFirm's (1) folder/naming conventions, (2) the HARD separation of the
> public version-controlled codebase from finance/company-sensitive data that must NEVER be
> committed or deployed, and (3) the organizer/librarian role that keeps both intact.
> Feeds **L2.A6**. Ties to A8.2/A8.3 (isolation/secrets), L1.B4.4 (PII boundary), A7.3 (fail-closed),
> A6.2 (audit). Grounded in CLAUDE.md §3.12, §5.6, §5.7.

## 1. The surveyed alternative space (full menu, then choose)

**(A) How to classify what is sensitive — the scheme menu** (sources 02, 03):
- Confidentiality-only national schemes (Confidential/Secret/Top-Secret, EO 13526) — REJECT (wrong
  domain).
- FIPS-199 CIA triplet `SC = {(confidentiality,impact),(integrity,impact),(availability,impact)}`,
  impact in {LOW,MODERATE,HIGH} + **high-water-mark** for systems — **ADOPT as the classification core.**
- Commercial 2–5-tier schemes (CISSP 5-tier; enterprise 3-tier) — ADOPT the **minimal-tiers** lesson:
  collapse to a 2-tier operational split (PUBLIC vs PRIVATE) + **secondary labels** (pii/finance/
  deal-doc/client) rather than many tiers (AWS explicit recommendation, source 03).

**(B) How to keep sensitive data out of the public repo — the enforcement menu**:
- **Structural:** gitignored private workspace (sources 01, 08) — necessary, NOT sufficient
  (.gitignore ignores only untracked files; it is *not* a security control, source 08).
- **Content-scanning gates:** Gitleaks (pre-commit+CI, regex+entropy), TruffleHog (history+verify),
  detect-secrets (baseline), GitGuardian (managed ML) — **ADOPT defense-in-depth across all four
  gates** (sources 04, 05); no single tool/gate.
- **Config externalization:** 12-factor — store config+credentials in **env/secret-manager**, never
  in files; the **litmus test** = repo open-sourceable anytime without leaking a credential
  (source 01) — **ADOPT as the boundary's correctness invariant.**
- **Encrypt-in-git (SOPS/git-crypt):** **REJECT as primary** for company data (encrypted blob still
  distributed; key-compromise exposes history). ADOPT only for bounded infra config; ADOPT at-rest
  encryption for the private store (source 09).
- **Data-store isolation:** enforce per-company isolation in the **data layer (RLS / schema- or
  DB-per-company)**, default-deny, unbypassable — NOT by application convention (source 10;
  CLAUDE.md §5.6). App-layer-only filtering = weakest, leak-prone, so REJECT.

**(C) Folder/naming conventions** (source 06): self-documenting, flow-ordered top-level dirs;
**no junk-drawer names** (CLAUDE.md §5.7); the **Go internal/ principle** — privacy enforced by
*mechanism* (compiler) not convention — is the transferable model for the boundary; configs/ =
templates only; avoid src/.

**(D) The organizer role** (source 07): DAMA-DMBOK **Owner / Steward / Custodian** split — model the
"organizer/librarian" as a **Data Steward agent** (keeps structure+boundary+metadata policy-
consistent), with the orchestrator as **Owner** (accountable, sets policy) and the storage layer as
**Custodian** (backup/encryption/retention). Separation = least-privilege (CLAUDE.md §5.6).

## 2. Concrete recommendation for AutoFirm (cited)

1. **One invariant rules the boundary — the 12-factor litmus test (source 01):** the public
   AutoFirm repo must be open-sourceable at any instant without leaking any credential, finance
   figure, client name, or per-company datum. Everything below exists to uphold it.

2. **Classify on the FIPS-199 confidentiality axis (sources 02, 03), collapsed to a 2-tier git
   boundary:** confidentiality >= MODERATE implies PRIVATE (never committed/deployed); else PUBLIC.
   Apply the **high-water-mark** at the workspace root (source 02): a workspace holding any
   MODERATE/HIGH artifact is wholly PRIVATE. Default-deny: unknown artifact = PRIVATE (source 03
   minimal-tiers + labels). Default-PRIVATE artifact list seeded from AWS Table 3 (trade secrets,
   M&A, pricing, contracts, HR, vendor bank details, CRM) — exactly AutoFirm's B15 client outputs.

3. **Public repo layout (source 06 + CLAUDE.md §5.7):** flow-ordered, self-documenting dirs;
   configs/ = *.example templates only; no utils/ or common/; 300-line file cap; structure-lint
   test. Per-company **private workspace is gitignored AND un-committable by mechanism** — the
   internal/ principle ported to data (source 06): a tool, not a convention, enforces it.

4. **Defense-in-depth boundary-guard (sources 04, 05, 08):** pre-commit Gitleaks -> CI gitleaks-action
   -> scheduled TruffleHog history scan -> provider scanning; custom .gitleaks.toml rules extended to
   finance/PII *data* patterns; fail-closed on any hit, logged to the append-only audit (A6.2);
   overrides require justification. If a breach occurs: **rotate -> history-rewrite -> force-push ->
   notify** runbook, human-gated (source 08).

5. **Store + isolation (sources 09, 10; CLAUDE.md §5.6):** PRIVATE data lives in a governed store
   with **encryption-at-rest** (KMS/age) and **data-layer tenant isolation** (RLS keyed on
   company_id; schema/DB-per-company for HIGH-confidentiality companies), default-deny,
   unbypassable by the agent layer. Config/credentials via **env/secret-manager**, never files
   (source 01). Encrypt-in-git only for bounded infra config (source 09).

6. **Organizer/librarian = Data Steward agent (source 07):** maintains taxonomy+naming, classifies
   artifacts, owns .gitignore/.gitleaks.toml allowlists, runs on the heartbeat (CLAUDE.md §4.7)
   to catch structure/boundary drift, logs every act, and **escalates rather than silently deletes**
   sensitive data (mirrors §3.8). Least-privilege separation from Owner (orchestrator) and Custodian
   (store ops).

## 3. Build implications (what changes in AutoFirm)
- **Components:** classification (FIPS-199 SC triplet + high-water-mark) -> boundary-guard
  (4-gate scanners) -> private-store (RLS + at-rest encryption) -> organizer-librarian steward
  agent -> breach-remediation runbook -> committed .gitleaks.toml + STRUCTURE.md + structure-lint.
- **Contracts:** every artifact = {tier: PUBLIC|PRIVATE, labels:[...], SC:{c,i,a}}; PUBLIC repo =
  code+templates only; PRIVATE = gitignored + governed store; isolation+secrets enforced by mechanism.
- **Tests-with-teeth (CLAUDE.md §3.6):** seeded-secret/finance fuzz across all 4 gates; boundary-exact
  LOW/MODERATE cutoff tests; red-team cross-tenant leak test (forged/missing tenant -> zero rows);
  authorization test (steward cannot commit/exfiltrate/un-audited-delete PRIVATE data); structure-lint
  (no junk-drawer names, <=300 lines). All mutation-tested.

## 4. Source map (per claim -> sources; >=3 for safety/correctness-critical)
- Litmus-test invariant: 01 (+ corroborated by 04, 08).
- Classification model (FIPS-199 formula, high-water-mark — CRITICAL): 02 (NIST primary) + 03 (AWS
  reproduction of NIST) + Wikipedia FIPS-199 reproduction = **>=3 independent**.
- Tier-count/labels: 03 (+ 02).
- Secret-scanning defense-in-depth (CRITICAL enforcement): 04 + 05 (Gitleaks primary) + 08.
- .gitignore limits + remediation: 08 (+ tool docs: git filter-repo, BFG).
- Folder/naming + enforced-privacy: 06 (+ CLAUDE.md §5.7).
- Encryption-at-rest / encrypt-in-git trade-off: 09.
- Data-layer tenant isolation (CRITICAL control): 10 (Postgres RLS primary) + Azure SQL RLS
  (Microsoft primary) + DZone/Leapcell expositions = **>=3 independent**.
- Organizer/librarian role: 07 (DMBOK) + >=3 corroborating DAMA-aligned expositions.

## 5. Open items deferred to Layer 2 (L2.A6 / L2.A8)
- The isolation-tier CHOICE (shared-schema+RLS vs schema/DB-per-company) per company-sensitivity is
  an L2.A8 branch-per-experiment with a golden metric — A6.4 fixes only the *principle* (data-layer,
  not convention).
- Whether to support any encrypt-in-git (SOPS) at all, or env/secret-manager exclusively, is an
  L2 design choice (A6.4 recommends env/secret-manager as default, SOPS bounded-only).
