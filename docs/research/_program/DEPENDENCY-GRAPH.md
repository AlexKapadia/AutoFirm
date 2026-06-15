# AutoFirm Research Dependency Graph (DEPENDENCY-GRAPH.md)

> The critical dependency edges between ontology questions, extracted from
> `QUESTION-ONTOLOGY.md` (which defines the questions and states each edge inline in every
> L2 entry’s `←` clause). This file is the visual recap; the ontology is the source of truth.

## Dependency graph (critical edges)

```
L1.A1,A2 ─┐
L1.B1.1  ─┼─► L2.A1 ─┐
L1.A3    ─┼─► L2.A3 ─┤
L1.A4,A6 ─┼─► L2.A4 ─┤
L1.A5    ─┼─► L2.A5 ─┼─► L3.PLATFORM ─┐
L1.A6    ─┼─► L2.A6 ─┤                │
L1.A7,A8 ─┼─► L2.A7 ─┤                ├─► L3.WHOLE
L1.A8    ─┼─► L2.A8 ─┤                │
L1.A9    ─┼─► L2.A9 ─┘                │
L1.B1,A1,A6,A7 ─► L2.ORG ────────────┘
L1.B2,B1     ─► L2.B2  ─┐
L1.B3,B4     ─► L2.B3  ─┤
L1.B4.1-4    ─► L2.B4  ─┤   (L1.B4.4 public-data sourcing/PII boundary gates L2.B4)
L1.B5.1,B4.2 ─► L2.B5  ─┤
L1.B6.1,B4.1 ─► L2.B6  ─┤
L1.B7.1,B4.2 ─► L2.B7  ─┤
L1.B8.1,B7.1 ─► L2.B8  ─┤   (marketing→sales handoff edge)
L1.B9.1,B8.1 ─► L2.B9  ─┼─► L3.BUSINESS ───► L3.WHOLE
L1.B10.1,A7  ─► L2.B10 ─┤
L1.B11.1,B4.3─► L2.B11 ─┤
L1.B13.*,A9  ─► L2.B13 ─┤   (client product/design + live-E2E)
L1.B14.*,A9.3,A7 ─► L2.B14 ─┤   (client software delivery/quality)
L1.B15.*,B4.1,A6.4 ─► L2.B15 ─┤   (models/decks/docs; writes to private workspace only)
L1.B12.*     ─► L2.B12 ─┘   (proven on the FIXED industry panel golden set)

L1.A1.5  ─► L2.ORG   (hiring/role-creation lifecycle: gap→spec→spawn→onboard→retire)
L1.A6.4,A8.2-3,B4.4 ─► L2.A6   (workspace layout + public/private data boundary + librarian)
```

**Cross-half edges (do not miss):** L1.B1.1 (org theory) feeds L2.A1 and L2.ORG — the platform's
orchestration IS organizational design. L1.A6/A7 (governance/safety) feed both halves: every
business playbook must run under the same audited, fail-closed governance as the platform.
