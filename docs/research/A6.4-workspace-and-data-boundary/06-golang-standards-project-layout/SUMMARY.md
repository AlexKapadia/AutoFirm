# SUMMARY — Standard Go Project Layout

## Full citation
- **Title:** *Standard Go Project Layout* (`golang-standards/project-layout`)
- **Author/Org:** golang-standards community (open-source; community convention, NOT an official
  Go spec — the repo states this caveat itself)
- **Year:** ongoing (widely referenced since ~2017)
- **Venue/Publisher:** GitHub — https://github.com/golang-standards/project-layout
- **URL:** https://github.com/golang-standards/project-layout

## Question(s) it informs
- **L1.A6.4** — the *folder-structure & naming conventions* half: self-documenting top-level
  directories whose names announce their contents, and a **compiler-enforced privacy** pattern
  (`/internal`) that is a direct analogue of AutoFirm's *enforced* (not by-convention) boundary.

## GRADE tier
- **Tier: Low–Moderate.** A community convention (the repo explicitly notes it is not officially
  defined by the Go maintainers), but extremely widely adopted and the de-facto reference for Go
  layout. The single hard, language-enforced fact — `/internal` is enforced by the **Go compiler**
  — is High-confidence (verifiable Go-toolchain behavior), independent of the convention's status.

## Key claims (exact where load-bearing)
1. **`/internal` (verbatim, load-bearing):** "Private application and library code. This is the code
   you don't want others importing in their applications or libraries. Note that this layout pattern
   is enforced by the **Go compiler itself**." → privacy by *mechanism*, not by *convention*.
2. **`/cmd`** — main applications, one subdir per executable; keep code minimal.
3. **`/pkg`** — library code "safe for external use" / importable by others.
4. **`/api`** — OpenAPI/Swagger/JSON-schema/protocol definitions.
5. **`/configs` (verbatim):** "Configuration file **templates** or default configs." (templates,
   not populated secrets — aligns with 12-factor, source 01.)
6. **`/docs`, `/test`, `/scripts`, `/build`, `/deployments`** — documentation; external test apps +
   `/test/data`; build/analysis scripts; packaging+CI configs; infra deployment configs.
7. **Anti-pattern (verbatim intent):** avoid **`/src`** — a Java-influenced pattern the Go community
   does not recommend.

## Up/down-rate reasoning
- Down-rated to Low–Moderate (community convention, self-declared non-official). **Up-rated** for the
  `/internal` compiler-enforcement claim, which is a hard, independently-verifiable toolchain fact.

## Reproducibility note
The `/internal` and `/configs` quotes are in the repo README; `/internal` enforcement is verifiable
by attempting to import an `internal/` package from outside its parent tree (the Go build fails).
