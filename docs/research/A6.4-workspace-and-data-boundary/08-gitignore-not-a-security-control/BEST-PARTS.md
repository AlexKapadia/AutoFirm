# BEST-PARTS — .gitignore Limits & Remediation → AutoFirm

## ADOPT
1. **Treat `.gitignore` as the FIRST layer, never the boundary itself.** AutoFirm's private
   workspace is `.gitignore`d AND scanned (sources 04/05) AND classified (02/03) AND stored in a
   governed store (10). The litmus test (source 01) is the *invariant*; `.gitignore` is one of
   several mechanisms that uphold it. **Build implication:** never let a sensitive datum rely on
   `.gitignore` alone — the boundary-guard must independently detect it.
2. **A documented, automated breach-remediation runbook**, fail-closed and audited:
   (1) **rotate/revoke immediately** (assume compromise the instant it hits history),
   (2) **rewrite history** with `git filter-repo` / BFG, (3) **force-push**, (4) **notify + log**
   to the append-only audit (A6.2). AutoFirm should automate detection→rotate→quarantine and
   require human sign-off for the history-rewrite + force-push (CLAUDE.md HITL).
3. **Assume already-tracked files are unprotected.** When AutoFirm onboards an existing repo, run a
   full-history scan (TruffleHog, source 04) FIRST — gitignoring later does nothing for what's
   already committed.

## REJECT / QUALIFY
- **Reject "delete the file and recommit" as remediation** — the source is explicit it does not
  remove the secret from history. Only rotate + history-rewrite is correct.
- **Qualify force-push** as a destructive op requiring approval + a backup ref (CLAUDE.md git
  hygiene) — never an unattended autonomous action.

## Concrete build implication
- **Component:** `breach-remediation` runbook/automation (detect → rotate → quarantine →
  human-gated history-rewrite → notify).
- **Contract:** any boundary-guard hit on already-committed data triggers the runbook fail-closed.
- **Test:** an integration test that commits a synthetic secret, then asserts the runbook rotates
  (mock), flags for rewrite, and logs — proving remediation works end-to-end.
