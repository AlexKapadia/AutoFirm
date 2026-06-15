# SUMMARY — SOPS & git-crypt: Encrypting Sensitive Files / Encryption-at-Rest

## Full citation
- **Title/Org (SOPS):** *SOPS (Secrets OPerationS)* — getsops community, **CNCF Sandbox project**
  (https://github.com/getsops/sops). Comprehensive guide: GitGuardian, *A Comprehensive Guide to
  SOPS* (https://blog.gitguardian.com/a-comprehensive-guide-to-sops/).
- **Title/Org (git-crypt):** *git-crypt — transparent file encryption in git*, Andrew Ayer
  (https://github.com/AGWA/git-crypt).
- **Year:** both ongoing/maintained.

## Question(s) it informs
- **L1.A6.4** — the option of keeping *some* sensitive material *version-controlled but encrypted*,
  vs. the strict "never commit" stance; and encryption-at-rest for the private store (CLAUDE.md §5.6).

## GRADE tier
- **Tier: Low–Moderate** (project docs + practitioner guide). SOPS being a CNCF Sandbox project and
  git-crypt's documented behavior are primary facts; the comparative guidance is practitioner-level.

## Key claims
1. **git-crypt:** "files you choose to protect are encrypted when committed and decrypted when
   checked out." Encrypts **entire files**; key management is **PGP (GPG)** keys you manage
   yourself (also supports symmetric key).
2. **SOPS:** "encrypts files before you commit them to Git." Crucially it **understands file
   structure (YAML/JSON/ENV) and encrypts only the VALUES, leaving the keys visible** — so diffs
   stay meaningful. Supports multiple key backends: **age, PGP, AWS KMS, GCP KMS, Azure Key Vault,
   HashiCorp Vault** (richer than git-crypt's PGP-only model).
3. **Best practice (corroborated):** apply least-privilege repo access, branch protection + reviews,
   and store decryption credentials (age keys / KMS tokens) in a secret store — never in the repo.
4. **Trade-off vs. "never commit":** encrypting-in-git keeps history + review workflow but adds
   key-management burden and a residual risk (encrypted blob is still distributed to everyone with
   repo access; compromise of a key exposes history).

## Up/down-rate reasoning
- Moderate for the tool-behavior facts (SOPS structure-aware value encryption; git-crypt whole-file
  PGP) — these are documented primary behaviors; Low for comparative "which is better" guidance.

## Reproducibility note
SOPS value-only encryption and multi-backend support, and git-crypt's whole-file PGP model, are in
the projects' READMEs; verifiable by encrypting a sample `.env` with each.
