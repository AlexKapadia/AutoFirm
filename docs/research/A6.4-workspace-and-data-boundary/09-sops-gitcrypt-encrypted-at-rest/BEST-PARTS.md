# BEST-PARTS — SOPS / git-crypt → AutoFirm

## ADOPT
1. **Encryption-at-rest for the private store is mandatory (CLAUDE.md §5.6).** Use **age/KMS-backed
   encryption** for the gitignored private workspace and the governed data store. SOPS' model is the
   reference: keys come from a KMS/secret-manager, never the repo.
2. **SOPS for the narrow, justified case of *config that benefits from review* (e.g. encrypted
   per-environment infra config)** — its **value-only encryption** keeps diffs/reviewable structure
   while hiding secrets. Prefer SOPS over git-crypt because of its **multi-backend KMS support**
   (age/AWS/GCP/Azure/Vault) and structure-awareness vs. git-crypt's PGP-only whole-file model.

## REJECT / QUALIFY (important boundary decision)
- **REJECT encrypted-in-git as the PRIMARY strategy for company-finance/PII/deal data.** A6.4's
  core stance (sources 01/08 + CLAUDE.md §3.12) is **never commit sensitive data at all** — not
  "commit it encrypted." Encrypted blobs are still distributed to everyone with repo access and a
  key compromise exposes the whole history irrevocably. So:
  - **Sensitive company DATA (finance/PII/deal docs/client files): NEVER committed, even encrypted**
    → gitignored private workspace + governed store with at-rest encryption + tenant isolation (10).
  - **Encrypted-in-git (SOPS): ONLY for small infra/config secrets where review history is valuable
    and the blast radius is bounded** — and even then env/secret-manager (source 01) is preferred.
- This keeps AutoFirm's litmus test intact: the public repo stays open-sourceable; SOPS files, if
  any, hold only bounded infra config, not company data.

## Concrete build implication
- **Component:** `at-rest-encryption` for the private store (KMS/age); optional `sops/` for bounded
  infra config only.
- **Contract:** company data ⇒ never in git (encrypted or not); infra config secrets ⇒ env/secret-
  manager preferred, SOPS-encrypted-in-git permitted only with KMS-backed keys + bounded scope.
- **Test:** assert no company-data artifact is ever git-tracked (even encrypted); assert any SOPS
  file decrypts only with the KMS key and contains no company-data classification label.
