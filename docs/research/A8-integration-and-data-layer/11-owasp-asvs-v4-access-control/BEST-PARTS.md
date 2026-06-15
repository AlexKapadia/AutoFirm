# BEST-PARTS — OWASP ASVS v4.0.3 Access Control (A8.2 corroboration + A8.2 test design)

## ADOPT
- **Trusted-layer enforcement as a stated requirement (V4.1.1)** — independent, non-vendor confirmation that access control (hence tenant isolation) must be enforced in a trusted server-side layer. This is the third leg corroborating the data-layer-not-convention rule alongside Postgres default-deny [#08] and the AWS RLS pattern [#07].
- **IDOR/cross-record test pattern (V4.2.1)** — adopt the four-verb cross-tenant probe directly as test cases: tenant A attempts to **create / read / update / delete** a row owned by tenant B; every attempt MUST be denied by RLS. This converts the abstract isolation claim into concrete, named adversarial tests.
- **Fail-securely requirement (V4.1.5)** — adopt as the assertion that *any* exception in the access path (missing tenant context, bad session var, connection as wrong role) results in **deny**, never open. Drives a negative test: unset `app.current_tenant` -> queries return zero rows / error, never all rows.

## REJECT
- **Client-side / convention-only access control** — ASVS V4.1.1 explicitly treats client-side controls as bypassable; matches our REJECT of app-layer-WHERE-clause-only isolation.

## DEFER
- ASVS V4.3 (other access-control admin requirements) — relevant to the eventual platform admin console, not the L1 data-layer foundation; revisit in L2.A8 / B13.

## CONCRETE BUILD IMPLICATION
- **Test it drives (cross-tenant IDOR matrix):** a parameterized E2E/integration test deriving from V4.2.1 — for every tenant-scoped table, run the create/read/update/delete-across-tenant matrix and assert **0 successful** cross-tenant operations. Pairs with the schema-audit test from #08 (structure) to give both *structural* and *behavioural* proof of isolation.
- **Invariant strengthened:** the A8.2 isolation claim now rests on **three independent sources** (Postgres primary [#08] + AWS [#07] + ASVS [#11]), satisfying DEPTH-RUBRIC §1 for a safety/correctness-critical control.
- **Generality:** ASVS is technology-agnostic, so the IDOR matrix test ports to any AutoFirm-built company regardless of datastore (Postgres RLS, or a Silo DB-per-tenant), keeping the contract general (CLAUDE.md §3.9).
