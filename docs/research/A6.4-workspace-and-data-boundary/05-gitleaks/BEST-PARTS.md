# BEST-PARTS — Gitleaks → AutoFirm

## ADOPT
1. **Gitleaks as the canonical pre-commit + CI secret gate.** Ship a committed `.gitleaks.toml` in
   the public repo with: default rules + **AutoFirm-specific rules** for *finance/company-sensitive*
   patterns (e.g. regexes for currency-amount tables, client-name registries, deal-doc markers) so
   the gate stops not only credentials but the **company-sensitive data** A6.4 is centrally about.
   **Build implication:** extend secret-scanning into data-leak-scanning via custom rules.
2. **Fail-closed commit blocking.** The "commit fails on hit; bypass only via explicit `SKIP=`"
   behavior is exactly the fail-closed posture CLAUDE.md §5.6 demands — adopt as-is; make `SKIP`
   require a logged justification.
3. **Allowlist discipline (`.gitleaksignore` fingerprints, `#gitleaks:allow`).** Use ONLY for proven
   false positives, each with a comment and an audit-log entry — the organizer/librarian owns the
   allowlist and reviews every entry (no silent suppression).
4. **gitleaks-action for CI** so the same ruleset runs server-side and can't be skipped locally.

## REJECT / QUALIFY
- **Reject regex+entropy as a COMPLETE boundary.** Gitleaks catches *patterned* secrets well, but
  free-form sensitive prose (a client's financials in a markdown memo) may evade regex. Therefore
  pair it with the **structural** boundary (gitignored private workspace, sources 01/08) so data
  never relies on content-matching alone. Content scanning is the *backstop*, not the *primary* line.

## Concrete build implication
- **Component:** committed `.gitleaks.toml` (default + AutoFirm finance/PII rules) + pre-commit +
  gitleaks-action CI job.
- **Contract:** any match ⇒ non-zero exit ⇒ blocked commit / failed CI, logged to audit.
- **Test:** unit tests asserting each custom rule fires on a synthetic positive and stays silent on
  a benign near-miss (boundary-exact), mutation-tested to kill an over-broad/over-narrow regex.
