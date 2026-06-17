# 07 — Organisational capability / competency growth modelling

> Workstream B4. The *domain* model: how organisations accrue capabilities as they
> hire, promote, re-scope, and shed roles. This grounds the W4 **`org_event →
> capability` projection** — capabilities are not invented, they *accrue from the
> audited org lifecycle*. Cross-links the existing repo research on auto-hiring &
> role creation rather than re-deriving it.

## Full citation

- **Cross-link (primary, already in repo):**
  `docs/research/A1.5-auto-hiring-role-creation/` — full library on how orgs hire /
  create roles, including:
  - `02-competency-gap-opm` — competency-gap analysis (capability accrues to fill a
    detected gap).
  - `04-role-episode-katz-kahn` — **Katz & Kahn role-episode model** (a role's
    expected behaviours = its capability surface; role-sending shapes it).
  - `09-raci-responsibility-assignment` — RACI (responsibility → who is
    Responsible/Accountable maps to which role holds which capability).
  - `11-halo-dynamic-role-instantiation` — dynamic role instantiation (roles, hence
    capabilities, created on demand).
  - `13-org-design-fit-burton-obel` & `SYNTHESIS.md` — org-design fit.
- **D. Teece, G. Pisano, A. Shuen, "Dynamic Capabilities and Strategic
  Management"**, *Strategic Management Journal*, **1997** — the canonical theory
  that a firm's capabilities are **path-dependent, accreted assets** reconfigured
  over time, not a fixed list. DOI: 10.1002/(SICI)1097-0266(199708)18:7<509::AID-SMJ882>3.0.CO;2-Z.
- **B. Kogut & U. Zander, "Knowledge of the Firm, Combinative Capabilities…"**,
  *Organization Science*, **1992** — capabilities grow *combinatorially* from
  recombining existing ones (supports "no ceiling, thousands of capabilities").

## Faithful structured summary (principles reproduced exactly)

**Capabilities are path-dependent accretions (Teece et al., 1997).** *Dynamic
capabilities* = *"the firm's ability to integrate, build, and reconfigure internal
and external competences."* Capabilities are *path-dependent*: what a firm can do
tomorrow is constrained and shaped by what it did (and hired/learned) up to today.
**Implication for W4:** the capability set at any time is a *function of the firm's
history* — exactly the event-sourcing replay model (source 01). The org's audit
trail *is* the path.

**Combinative growth (Kogut & Zander, 1992).** New capabilities arise from
**recombining** existing capabilities/knowledge. Growth is therefore *combinatorial*
and unbounded in principle — a firm does not pick from a fixed menu. **Implication:**
W4 must not encode a finite enum; the capability space is open and grows as roles
recombine responsibilities.

**Role episode → capability surface (Katz & Kahn; RACI).** A role's *expected
behaviours* (its responsibilities) define what it can be relied on to do — its
capability surface. RACI formalises the responsibility-to-role mapping. **This is
precisely AutoFirm's existing model:** `RoleCharter.responsibilities` →
(deterministic keyword extraction) → `RoleCapability`. A role's capabilities are a
faithful, deterministic function of its declared responsibilities.

**Capability accrual events (the org lifecycle).** Organisations gain/lose
capability through discrete lifecycle events:
- **Hire / auto-create-on-gap** → new role → new capabilities accrue (a *competency
  gap* detected → role instantiated to fill it — see `02-competency-gap-opm`,
  `11-halo`).
- **Promote / re-scope** → responsibilities change → capability surface shifts.
- **Fire / RIF** → capability withdrawn (but the *history* of having held it remains).

These map 1:1 to AutoFirm's `OrgEventKind` = `ROLE_HIRED / ROLE_AUTO_CREATED /
ROLE_RESCOPED / ROLE_FIRED / REPORTS_REASSIGNED`, each already appended to the
gapless, immutable `OrgAuditTrail`.

## Best parts to take (mapped to the W4 design)

1. **`org_event → capability` projection is the accrual model.** Each org lifecycle
   event deterministically projects to capability deltas: HIRED/AUTO_CREATED →
   `CAPABILITY_GRANTED`, RESCOPED → `CAPABILITY_GRANTED` + `CAPABILITY_RETIRED`
   (the diff), FIRED → `CAPABILITY_RETIRED`. The projection is the formal
   realisation of path-dependent capability accrual. *Maps to:* W4 core projection.
2. **No enum — open, combinatorial capability space.** Per Kogut & Zander, never
   bound the capability set by a hardcoded list; it grows as responsibilities are
   declared and recombined. *Maps to:* W4 generality (thousands, no ceiling).
3. **History is retained even after retirement (Teece path-dependence).** A FIRED
   role's capability is *retired*, not erased — the append-only log preserves that
   the firm once held it (org-evolution replay can show capability rise *and* fall).
   *Maps to:* W4 "growth log" + append-only.
4. **Gap → role → capability is already wired.** AutoFirm's `auto_create_on_gap`
   (competency-gap → new role) is the accrual trigger; W4 simply projects its audit
   event into the capability growth log. *Maps to:* reuse, no new mechanism.
5. **Responsibilities are the single source of capability (Katz–Kahn/RACI).** Keep
   capabilities a *pure deterministic function* of `RoleCharter.responsibilities`
   (as `role_capability_index.py` already does) so the model generalises to any
   company's role set. *Maps to:* W4 generality + determinism.

## Cross-links

- **01** event sourcing — the replay mechanism that realises path-dependence.
- Repo: entire `A1.5-auto-hiring-role-creation/` library (gap → hire → capability).
- Repo: `B1-organizational-operating-models/` (Galbraith, Mintzberg, Burton–Obel).
