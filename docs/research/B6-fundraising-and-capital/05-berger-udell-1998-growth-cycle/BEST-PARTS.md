# BEST-PARTS — Berger & Udell (1998)

## ADOPT

- **Adopt the financial growth cycle as the PRIMARY conditioning variable of the fundraising
  playbook.** The recommended instrument menu must be a function of the client's **life-cycle
  position** (age, size, information opacity), not a fixed default. This is the academic backbone for
  "stage norms" and makes the playbook general across industries while still stage-aware.
- **Adopt the stage -> source mapping as the engine's lookup spine:**
  - opaque/infant -> insider, friends/family, trade credit, angels;
  - adolescent/some-track-record -> VC, bank/intermediated debt;
  - mature/transparent -> public equity & debt, commercial paper.
- **Adopt information opacity as the gating constraint** linking this source to the pecking order
  (03): the more opaque the firm, the higher up the equity/insider end of the menu it sits.

## REJECT

- **Reject treating the cycle as time-linear or industry-uniform.** Firms traverse the cycle at very
  different *speeds* and may skip stages (a capital-light SaaS may reach VC fast; a services firm may
  never need VC at all). So map by **opacity/size/assets, not by calendar age** alone.

## Concrete build implication

- **Component:** `growth_cycle_stage_classifier` -> takes age, revenue, assets/tangibility, and an
  opacity proxy -> emits a stage label that gates `financing_source_ranker` (source 03's component).
- **Contract:** the stage label is an explicit, explainable input to every financing recommendation
  ("recommended angels/SAFE because firm is information-opaque pre-revenue").
- **Test:** run all 8 B12 panel rows through the classifier and assert each gets a *sensible*
  stage-appropriate menu (e.g. asset-heavy manufacturing unlocks bank debt earlier than digital
  marketplace) — the generality golden-set check (CLAUDE.md §4.5).
