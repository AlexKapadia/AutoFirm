# SUMMARY — UI State Coverage: Loading, Empty & Error States

## Full citation
- **(A) Title:** Loading, error and empty states pattern — Australian Government Agriculture
  Design System
  - **URL:** https://design-system.agriculture.gov.au/patterns/loading-error-empty-states
  - **Author/Org:** Australian Government (Dept. of Agriculture) — government design system
- **(B) Title:** Skeleton Screens / progress indicators & "Visibility of System Status"
  - **Author/Org:** Nielsen Norman Group (NN/g) — corroborates via Heuristic 1 (source 01)
  - **URL:** https://www.nngroup.com/articles/progress-indicators/ ·
    https://www.nngroup.com/articles/empty-state-interface-design/
- **(C) Title:** UI best practices for loading, error, and empty states — LogRocket
  - **URL:** https://blog.logrocket.com/ui-design-best-practices-loading-error-empty-state-react/
- **Year:** ongoing / current
- **Venue/Publisher:** government design system + NN/g (practitioner authority) + engineering blog

## Questions it informs
- **L1.B13.3** (state coverage: loading/empty/error/edge; nothing-static — PRIMARY for the
  state-coverage requirement)

## GRADE tier: Moderate
Anchored by a government design system (institutional, maintained) and NN/g (the state-coverage
need derives from Heuristic 1, source 01 = High). The engineering blog is supporting color only.
The CONCEPT (data-driven UIs have >=4 states) is corroborated across multiple independent design
systems; the underlying principle (visibility of system status) is High-tier via Nielsen.

## Key claims (exact)

**Every data-driven view has multiple states; design all of them.** Any view that fetches or
mutates data has at minimum: a **loading** state (data in flight), an **empty** state (request
succeeded, no content), an **error** state (request failed), and the **ideal/populated** state.
Edge variants (partial, paginated, offline, slow) extend this.

**Loading state.** Communicates the system is working, preventing "is it stuck?" doubt. "Skeleton
screens are placeholders that resemble the content being loaded, making the interface feel more
responsive." This is a direct application of Nielsen Heuristic 1 (Visibility of system status,
source 01) — for waits, show determinate progress where possible.

**Empty state.** "An empty state is the screen design or UI state a user sees when there's no
content to display" — but "it shouldn't be literally empty": it should explain why it's empty and
guide the user to the next action (first-run onboarding, a CTA). An empty state is a UX opportunity,
not a blank screen.

**Error state.** "Error states inform users of issues and guide them on how to resolve the problem
or retry the action." Best practice: plain-language message, include an error code where useful, and
provide a retry mechanism (a button to re-fetch). This is Nielsen Heuristics 9 (recover from errors)
+ 5 (error prevention), source 01.

**Consistency & reuse.** "UX/UI consistency across the application is really important … standardize
the way data-fetching states are handled" — build loading/empty/error as reusable components
separated from main content (ties to atomic design, source 06; Nielsen H4 consistency, source 01).

## Reproducibility note
The four-state model (loading/empty/error/ideal), skeleton-screen definition, "not literally empty"
empty-state rule, and retry-mechanism error-state rule are stated across the cited government design
system and NN/g articles, and re-verifiable there. The principle traces to Nielsen H1/H5/H9.
