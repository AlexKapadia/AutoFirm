# BEST-PARTS — Secret-Scanner Comparison → AutoFirm

## ADOPT
1. **Defense-in-depth across all four gates** (not one tool). AutoFirm's boundary-guard runs:
   (a) **pre-commit** hook (fast, blocks the commit), (b) **CI** diff scan (catches bypassed
   commits), (c) **scheduled full-history** scan (catches anything pre-existing), (d) **provider**
   secret scanning. **Build implication:** if the pre-commit gate is skipped (`SKIP=`), the CI gate
   still fails closed — no single-point bypass.
2. **Gitleaks for the pre-commit + CI gates** (fast, regex+entropy, simple `.gitleaks.toml`) and
   **TruffleHog for scheduled history scans** (verification + 700+ types). This split matches each
   tool to its strongest role and is the documented startup-profile recommendation.
3. **detect-secrets `--baseline`** as the mechanism to onboard an EXISTING repo (accept current
   state, then block *new* findings) — useful when AutoFirm first wraps a pre-existing codebase.

## REJECT / QUALIFY
- **Reject relying on any single scanner or on the FP percentages as acceptance numbers.** The
  1–3% / 5–15% figures are practitioner estimates (Low tier) — do NOT bake them into a gate
  threshold. The gate's correctness is proven by AutoFirm's own seeded-secret test (below), not by
  a vendor FP figure.
- **Qualify GitGuardian (paid platform):** adopt only if/when AutoFirm needs managed ML filtering at
  scale; the open-source Gitleaks+TruffleHog pair covers the core need.

## Concrete build implication
- **Component:** `boundary-guard` = pre-commit (Gitleaks) + CI (Gitleaks action) + cron
  (TruffleHog history) + provider scanning, all reporting to the append-only audit log (A6.2).
- **Contract:** a hit on ANY gate fails closed (CLAUDE.md §5.6) and is logged; overrides
  (`#gitleaks:allow`, `SKIP=`) are themselves audit events requiring justification.
- **Test (tests-with-teeth):** a property/fuzz test that injects synthetic AWS keys, API tokens, and
  finance figures into staged/committed/historical positions and asserts each of the four gates
  catches its class — mutation-tested so a weakened regex/threshold is killed (CLAUDE.md §3.6).
