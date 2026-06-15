# SUMMARY — The Twelve-Factor App, Factor III: Config

## Full citation
- **Title:** The Twelve-Factor App — *III. Config: Store config in the environment*
- **Author/Org:** Adam Wiggins (originally, at Heroku) / the twelve-factor community
- **Year:** 2011 (v1.0; site maintained since)
- **Venue/Publisher:** https://12factor.net/config
- **URL:** https://12factor.net/config (retrieved 2026-06-15)

## Question(s) it informs
- **L1.A6.4** — public version-controlled codebase vs. private sensitive data; the *litmus test*
  for whether the boundary is correct.
- Ties to L1.A8.3 (secrets/credential scoping) and CLAUDE.md §5.6 (secrets via env/secret-manager
  only, never in repo).

## GRADE tier
- **Tier: Low–Moderate.** It is a widely-adopted, named, primary methodology document (the canonical
  statement of the principle, not a third-party summary), but it is a practitioner manifesto, not a
  peer-reviewed paper or standard. **Up-rated** to "Moderate for this one claim" because the specific
  litmus-test claim it anchors is independently corroborated by the secret-scanning and
  gitignore-remediation literature (sources 04, 08) and is the de-facto industry baseline.
  Used here only for the design-principle claim, not for any quantitative claim.

## Key claims (exact wording where load-bearing)
1. **Definition of config (verbatim):** config is *"everything that is likely to vary between deploys
   (staging, production, developer environments, etc)."* This explicitly includes *"resource handles
   to databases and other backing services, credentials to external services, and per-deploy values
   such as the canonical hostname."*
2. **The litmus test (verbatim, load-bearing):** *"A litmus test for whether an app has all config
   correctly factored out of the code is whether the codebase could be made open source at any
   moment, without compromising any credentials."*
3. **The mechanism (verbatim):** *"The twelve-factor app stores config in environment variables"* —
   chosen because env vars are language/OS-agnostic and *"won't accidentally enter version control."*
4. **Critique of config files:** even untracked config files (e.g. `config/database.yml`) are
   discouraged because they "have a tendency to be checked into the repo by mistake," and they
   scatter and proliferate per-language/per-framework.

## Reproducibility note
A reviewer can re-derive every quote by fetching https://12factor.net/config (cached/stable page).
The litmus test is the section's headline claim and appears verbatim on the page.
