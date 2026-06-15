# SUMMARY — .gitignore Is Not a Security Control; Leaked-Secret Remediation

## Full citation (multiple corroborating primary/practitioner sources)
- *Mitigating Secret Leaks: Why .gitignore is Not a Security Strategy* — Dev|Journal, 2026-04-11
  (https://earezki.com/ai-news/2026-04-11-oops-i-leaked-secrets-gitguardian-warned-me-/)
- *Don't Let Hardcoded Secrets Compromise Your Security: 4 Effective Remediation Techniques* —
  Cycode (https://cycode.com/blog/dont-let-hardcoded-secrets-compromise-your-security-4-effective-remediation-techniques/)
- **Primary tools referenced:** `git filter-repo` (Git project) and **BFG Repo-Cleaner**
  (https://rtyley.github.io/bfg-repo-cleaner/) — the canonical history-rewrite tools.
- **Year:** 2026 (and tool docs, ongoing).

## Question(s) it informs
- **L1.A6.4** — the *limits* of the structural boundary: `.gitignore` is necessary but NOT
  sufficient; defines the fail-state remediation when the boundary is breached.

## GRADE tier
- **Tier: Low–Moderate** (practitioner sources) but the core facts are **mechanically true and
  uncontested** (verifiable Git behavior + documented tool capabilities), so the load-bearing
  claims are effectively High-confidence; corroborated across multiple independent sources.

## Key claims
1. **`.gitignore` only affects UNTRACKED files.** "Git persists in tracking any file that was
   committed prior to being added to the ignore list." → an already-tracked or already-committed
   secret is NOT protected by `.gitignore`. (Mechanically verifiable Git behavior.)
2. **`.gitignore` is not a security control** — it prevents accidental *addition*, not *exposure*;
   it cannot remove what is already in history.
3. **Remediation sequence when a secret is committed (order matters):**
   (a) **Revoke/rotate immediately** — "the absolute first step… invalidate the compromised API
   key, token, or credential at its source" (the secret must be assumed compromised the moment it
   hits history);
   (b) **Rewrite history** — "use a tool like BFG Repo-Cleaner or `git filter-repo` to permanently
   remove the sensitive data from the entire Git history" ("Deleting the file is not enough");
   (c) **Force-push** the rewritten history;
   (d) **Notify** security/audit.
4. **Layered defense** is the recommended posture: `.gitignore` + pre-commit scan + CI scan + secret
   manager + periodic audit (corroborates sources 01/04/05).

## Up/down-rate reasoning
- Up-rated: the central claims are verifiable Git mechanics + documented tool behavior, agreed
  across independent sources; down-rated only for the practitioner (non-peer-reviewed) venue.

## Reproducibility note
A reviewer can confirm claim 1 by `git add` of a previously-committed file after gitignoring it
(Git still tracks it); BFG/`git filter-repo` capabilities are in their official docs.
