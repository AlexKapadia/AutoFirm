# SUMMARY — Secrets-Scanner Comparison (detect-secrets vs Gitleaks vs TruffleHog vs GitGuardian)

## Full citation
- **Title:** *detect-secrets vs Gitleaks vs TruffleHog vs GitGuardian (2026): Pre-Commit, CI and
  History Coverage Compared*
- **Author/Org:** NomadX / DevSecOps.ae
- **Year:** 2026
- **Venue/Publisher:** devsecops.ae (practitioner comparison)
- **URL:** https://devsecops.ae/secrets-scanners-comparison-2026/

## Question(s) it informs
- **L1.A6.4** — the *enforcement layer* of the boundary: which tools stop a secret/sensitive value
  from ever entering the public repo, across the defense-in-depth gates (pre-commit, CI, history).

## GRADE tier
- **Tier: Low** (practitioner comparison, vendor-adjacent). Used for the **defense-in-depth model**
  and **tool-role mapping**, which are independently corroborated by sources 05 (Gitleaks primary
  docs) and 08 (gitignore-remediation). Quantitative false-positive ranges are treated as
  indicative, not authoritative, and are explicitly NOT relied upon as critical numbers.

## Key claims
1. **Four-gate defense-in-depth model:** pre-commit hook → CI diff scan → scheduled full-history
   scan → platform/provider scanning (e.g. GitHub Secret Scanning). "Most teams run at least two
   scanners in combination… Real programmes deploy all four [gates]."
2. **Tool-role mapping:**
   - **Gitleaks** — "the fastest open-source secrets scanner — typically under a second on modest
     diffs"; "ideal as a pre-commit hook" and CI diff scanner. (Regex + entropy; see source 05.)
   - **detect-secrets** — "clean pre-commit integration"; baseline workflow (`--baseline`) "lets you
     accept the current state of the repo as 'all known issues'" — best for onboarding legacy repos.
   - **TruffleHog** — strongest at **git-history** scanning + **credential verification**: its
     "verifier modules validate 700+ secret types by making safe read-only API calls" (e.g. an AWS
     `GetCallerIdentity` call to confirm a key is live).
   - **GitGuardian** — ML filtering "reduces false positives to 1–3% out of the box"; positioned as
     the enterprise platform.
3. **Indicative false-positive ranges (NOT relied upon):** Gitleaks ~5–15%; TruffleHog without
   verification ~10–20%; GitGuardian ~1–3%; detect-secrets w/ baseline ~0–5%; with verification
   "rates drop below 2% for live secrets."
4. **Recommendation (startup profile):** "Gitleaks pre-commit + CI, TruffleHog quarterly git-history
   scan, GitHub Secret Scanning enabled."

## Up/down-rate reasoning
- Down-rated to Low (practitioner blog). The architectural claims (defense-in-depth gates; tool
  roles) are corroborated by the Gitleaks primary repo (source 05) and the broad secret-leak
  literature; the percentage FP figures are kept as context only.

## Reproducibility note
Tool roles and the four-gate model are restated across the secret-scanning literature; the specific
quotes are on the linked page. Gitleaks' regex+entropy and pre-commit role are confirmed primary
in source 05.
