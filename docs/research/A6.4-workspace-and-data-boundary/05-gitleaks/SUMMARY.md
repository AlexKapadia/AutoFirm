# SUMMARY — Gitleaks (primary project documentation)

## Full citation
- **Title:** *Gitleaks — Find secrets with Gitleaks* (README / project docs)
- **Author/Org:** Zachary Rice et al. (gitleaks/gitleaks), open-source (MIT)
- **Year:** project ongoing; behavior current as of v8.x (2026)
- **Venue/Publisher:** GitHub — https://github.com/gitleaks/gitleaks
- **URL:** https://github.com/gitleaks/gitleaks

## Question(s) it informs
- **L1.A6.4** — the concrete, primary mechanism for the pre-commit + CI enforcement gate that keeps
  secrets out of the public repo.

## GRADE tier
- **Tier: Moderate** (primary project documentation of a widely-deployed open-source tool — the
  authoritative source for how Gitleaks itself behaves).

## Key claims (from the primary docs)
1. **What it is (verbatim):** "a tool for **detecting** secrets like passwords, API keys, and tokens
   in git repos, files, and whatever else you wanna throw at it via `stdin`."
2. **Detection method:** **Golang regex** rules + **Shannon-entropy** thresholds ("a minimum shannon
   entropy a regex group must have to be considered a secret"). Companion post: "Regex is (almost)
   all you need."
3. **Pre-commit hook:** installable via `.pre-commit-config.yaml`; runs before each commit; on a
   hit the commit fails ("Detect hardcoded secrets…Failed"); bypassable only with `SKIP=gitleaks
   git commit` (i.e. an explicit, auditable override).
4. **CI:** integrates via the official **gitleaks-action** GitHub Action for CI scanning.
5. **Config `.gitleaks.toml`:** rules carry id/description, regex, secret-group, entropy threshold,
   path-filter regex, and keyword pre-filters. **Allowlists:** rule-level `[[rules.allowlists]]`,
   global `[[allowlists]]` (higher precedence), inline `#gitleaks:allow`, and `.gitleaksignore`
   fingerprints.
6. **Modes:** `detect`/`protect` deprecated in v8.19.0 in favor of `git`, `dir`, `stdin` subcommands.

## Up/down-rate reasoning
- Moderate: primary docs for the tool's own behavior; no conflicting source. The "fastest scanner"
  speed claim originates from a third-party comparison (source 04) and is treated as indicative.

## Reproducibility note
All behaviors are documented in the linked README/docs; a reviewer can install the pre-commit hook
and confirm the fail-on-secret behavior and `.gitleaks.toml` allowlist semantics directly.
