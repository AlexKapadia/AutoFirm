# W4 — Dynamic Capability Registry: design, generality & security spec

> **Status:** research-phase design synthesis (CRO). Distils sources 01–08 in this
> folder into the W4 design. Not an implementation; it is the contract the build
> phase works against. Grounded in the existing code: capabilities are derived
> deterministically from `RoleCharter.responsibilities` via
> `src/autofirm/frontdoor/role_capability_index.py`, and the org lifecycle
> (`src/autofirm/org/org_lifecycle_engine.py`) emits `OrgEventKind`
> (`ROLE_HIRED / ROLE_AUTO_CREATED / ROLE_RESCOPED / ROLE_FIRED /
> REPORTS_REASSIGNED`) onto a gapless, immutable `OrgAuditTrail`.

W4 replaces a hardcoded capability/feature list with a **dynamic, evolving registry**
that grows as the org hires / promotes / re-scopes / fires, **recorded
append-only & tamper-evidently, derived by pure replay, and shown visually.**

---

## 0. One-paragraph architecture

The org lifecycle emits audited `OrgEvent`s. A **pure, deterministic projection**
(`org_event → capability`) turns each org event into capability deltas, appended as
`CapabilityRegistryEvent`s onto an **append-only, gapless, RFC-6962 hash-chained
growth log**. The **live registry is not stored** — it is the **pure replay (left
fold)** of that log. Several **read-model projections** (growth timeline,
role→capability graph, count-over-time) are regenerated on demand from the one log
for the evidence/showcase. A capability becomes **loadable** only when its
descriptor is **signed, verified, and within its declared least-privilege bound**;
verification failure is **fail-closed**.

---

## 1. How growth is RECORDED

### 1.1 `CapabilityDescriptor` (the unit)
A versioned, additive, NL-declared descriptor (sources 03 MCP `server.json`, 04
SKILL.md frontmatter):

```
CapabilityDescriptor:
  capability_id      # unforgeable: H(namespace || name)  (sources 04/05/08)
  namespace          # emitting role/org identity (publisher+name model, source 08/03)
  name               # short, lowercase-hyphen, unique within namespace
  description        # NL "what + when" — the discovery surface (source 04)
  keywords           # frozenset, deterministically extracted from responsibilities
                     #   (reuses extract_capability_keywords in role_capability_index.py)
  declared_authority # point in capability lattice over scoped resources (source 05)
  schema_version     # additive evolution only (source 03)
  origin_role_id     # provenance to the audited org event
```
`capability_id` and `keywords` are **pure functions** of inputs (order-independent),
preserving the existing determinism guarantee (§3.11).

### 1.2 `CapabilityRegistryEvent` (the append-only growth log)
One immutable, sequence-numbered, hash-chained record per capability delta:

```
CapabilityRegistryEvent (frozen):
  seq          # gapless monotonic == position in log (reuse OrgAuditTrail invariant)
  kind         # CAPABILITY_GRANTED | CAPABILITY_RETIRED | DESCRIPTOR_REVISED | PROJECTION_REFUSED
  descriptor   # the CapabilityDescriptor (or its id for RETIRED)
  org_event_seq# the OrgEvent.seq this delta was projected from (provenance link)
  prev_hash    # entry_hash of seq-1  (genesis: domain constant)
  entry_hash   # H(domain || prev_hash || serialize(this))   (source 02 / RFC 6962)
```

**Recording rules** (sources 01, 02):
- **Append-only.** Never mutate/delete; a withdrawn capability is a *new*
  `CAPABILITY_RETIRED`, a changed declaration is a *new* `DESCRIPTOR_REVISED`
  (version-bound, triggers re-verification — source 06 Consent-Abuse defense).
- **Gapless seq.** `event.seq == len(log)`; non-consecutive seq is **refused
  (fail-closed)**, mirroring the existing `OrgAuditTrail.append`.
- **Hash-chained.** `entry_hash` commits to all prior events; the **head hash** is
  the single publishable commitment to the entire growth history.
- **Refusals are audited.** A projection that cannot proceed (e.g. unverifiable
  descriptor) appends `PROJECTION_REFUSED` — the log proves the system refused.

### 1.3 `org_event → capability` projection (pure, total, deterministic)
| OrgEventKind | Capability delta |
|---|---|
| `ROLE_HIRED` / `ROLE_AUTO_CREATED` | `CAPABILITY_GRANTED` for each capability derived from the new charter's responsibilities |
| `ROLE_RESCOPED` | diff old vs new responsibilities → `CAPABILITY_RETIRED` (dropped) + `CAPABILITY_GRANTED` (added) |
| `ROLE_FIRED` | `CAPABILITY_RETIRED` for that role's capabilities |
| `REPORTS_REASSIGNED` | no capability delta (org-structure only) |

Reuses `extract_capability_keywords` / `RoleCapabilityIndex.from_org_state` — the
projection is the *existing* derivation, re-expressed as an event stream.

### 1.4 Live registry = pure replay (source 01)
```
live_registry = fold(apply_capability_event, EMPTY, log)
```
`apply_capability_event(state, event)` is pure (no I/O/clock/randomness). **There is
no stored "current capability set"** — only the fold. Snapshots, if added at scale,
are **cache only** and must satisfy `snapshot_k == fold(EMPTY, log[:k])` or be
rejected (fail-closed). Replaying to any `seq` reconstructs any historical state
(org-evolution replay).

---

## 2. How growth is SHOWN (evidence / showcase)

Three independent **CQRS read-model projections** of the one log (source 01), each
regenerated on demand → feed `evidence/` (PNG + interactive HTML per CLAUDE.md
§3.10):

1. **Capability-growth-over-time timeline** — step series of cumulative capability
   count vs `seq`/timestamp; grants rise, retirements fall. Proves accrual *and*
   path-dependent decline (source 07 Teece).
2. **Live role→capability graph** — bipartite graph (roles ↔ capabilities)
   **regenerated entirely from the replayed registry**, never hand-maintained.
   Black-&-white aesthetic per §3.10.
3. **Org-evolution replay** — animate/step the registry state across `seq` to show
   the org's capability surface evolving as it hired/re-scoped/fired.
4. **Head hash + ASBoM export** — publish the chain head and a CycloneDX-style
   capability bill-of-materials as audit artifacts (source 06).

Analysis/plotting deps live in the **analysis-only** manifest, never runtime (§3.10).

---

## 3. GENERALITY guarantee + test approach

**Guarantee.** The registry works for **any company, any role set, any number of
capabilities (thousands, no ceiling), with no per-scenario magic constants.** It
holds because: capabilities are a *pure deterministic function* of declared
responsibilities (no enum — sources 04/07/08); the space is *open & combinatorial*
(source 07 Kogut–Zander); state is a *fold over a log* (source 01) so size is
bounded only by the log; descriptors are *schema-versioned & additive* (source 03)
so new capability kinds need no migration.

**No-overfit rule (CLAUDE.md §3.9).** No hardcoded capability list, no fixed enum of
allowed capabilities, no constant tuned to a sample company, no special-casing of
golden roles. Correctness is argued from **invariants**, then property-tested.

**Test approach (CLAUDE.md §3.6 — adversarial + property + combinatorial + mutation):**
- **Property — replay determinism:** for arbitrary valid org-event sequences,
  `fold(log)` is identical across N≥1000 repeats and across processes.
- **Property — projection purity:** identical org-event sequence ⇒ identical
  capability log (incl. identical hashes); shuffling *responsibility order within a
  charter* does **not** change the derived capabilities (order-independence already
  in `extract_capability_keywords`).
- **Property — append-only / gapless:** generated event streams always have
  `seq == index`; any injected gap/reorder is refused (fail-closed).
- **Property — hash-chain integrity:** for random logs, recomputed chain == stored
  chain; any single-event mutation/insert/delete/reorder is detected (DY-Skill
  *modify/drop* ops, source 06).
- **Metamorphic — grant∘retire:** `GRANT(c)` then `RETIRE(c)` leaves `c` absent from
  live registry but **present in history**; FIRED→re-HIRED restores it as a *new*
  granted event (history preserved).
- **Combinatorial / scale:** generate orgs with up to **thousands of roles ×
  responsibilities** (Hypothesis + parametrised); assert no ceiling, linear-ish
  replay cost, and a documented O(n) (or O(n) + O(log n) proof) scaling curve in
  `evidence/` — explicitly proving generality, not a fixed-size fixture.
- **Cross-company generality:** run the *same* engine over ≥3 structurally
  different synthetic companies (flat / deep / matrix) + the public-data E2E
  companies; assert identical engine, zero per-company branches.
- **Mutation testing (`mutmut`):** target ≈100% on the projection, the fold, the
  hash chain, and the verification gate; survivors get a harder adversarial test.

---

## 4. SECURITY controls for dynamic capability loading

A capability existing in the log ≠ a capability being **loadable**. Loading is
gated, signed, verified, least-privilege, and **fail-closed** (sources 05/06/08;
CLAUDE.md §5.6).

1. **Signed.** Every loadable descriptor carries a signature chained to the audited
   `OrgEvent` that conferred it (Sigstore-style provenance; SLSA L3–L4 target,
   source 06). A capability that cannot be traced to an audited org event is not
   loadable.
2. **Verified on load (fail-closed).** Before loading: (a) verify the hash chain end
   to-end; (b) verify the signature; (c) verify `live_registry` membership by
   replay. **Any failure ⇒ refuse to load** + append `PROJECTION_REFUSED`. Never
   degrade-open. A snapshot disagreeing with replay is rejected.
3. **Least-privilege / confinement.** Runtime authority is upper-bounded by
   `declared_authority` (capability lattice, source 05 Theorem 5.6 / `Permits()`).
   Access outside the transitive closure is denied. FIRED role → authority drops to
   lattice bottom (no ambient authority).
4. **Version-bound trust + delta re-approval.** Trust binds to the descriptor's
   exact content hash; any `DESCRIPTOR_REVISED` forces re-verification — a
   once-trusted capability is **not** forever-trusted (source 06 Consent-Abuse).
5. **Untrusted-by-default discovery.** NL descriptions are *data, not instructions*;
   never injected into operator context unverified (source 06 prompt-injection-via
   -skill — the dominant exploited vuln). Structured separation of capability
   declaration from agent instructions.
6. **Threat model = DY-Skill (source 06, Def 3.5):** intercept / inject / modify /
   drop / forge / compromise-registry. Hash chain defeats modify/drop/reorder;
   signing defeats forge/inject; gapless seq defeats drop; fail-closed defeats
   degrade-open. Update `docs/threat-model.md` accordingly.

---

## 5. RED flags / open risks to resolve in build

- **Existing `OrgAuditTrail` is gapless but NOT yet hash-chained.** W4 must *add*
  RFC-6962 `prev_hash`/`entry_hash` (to the capability log, and ideally retrofit the
  org trail) — do not assume tamper-evidence already exists. Confirmed by reading
  `org_lifecycle_events.py` (seq invariant present; no hashing).
- **Signing key custody.** Provenance signatures need a key source; must be
  env/secret-manager, least-privilege, never in logs (§5.6). Define before build.
- **Prompt-injection-via-description.** Capability `description` is NL and flows to
  agents; it must be treated as untrusted data with structured separation, or it
  reintroduces the exact vuln source 06 documents at scale (42,447 skills).
- **Snapshot trust.** If snapshots are introduced for scale, they are cache-only and
  must be re-derivable from the log; a forged snapshot must never become truth.
- **Naming-collision risk** with sibling B-series folders (noted in repo memory) —
  this folder is `B4-capability-registries`; keep it distinct.

---

## 6. Source map (this folder)

| # | Source | W4 role |
|---|---|---|
| 01 | Fowler Event Sourcing + Young CQRS | append-only stream; current state = pure replay; read-model projections |
| 02 | RFC 6962 hash-chain (+ Haber–Stornetta, Crosby–Wallach) | tamper-evident growth log; head-hash commitment |
| 03 | MCP Registry (AAIF) | descriptor metadata, schema-versioning, federation, trust-boundary lesson |
| 04 | Anthropic Agent Skills | NL capability packaging, progressive disclosure, versioning |
| 05 | Capability-based security (Dennis–Van Horn; SkillFortify lattice) | unforgeable, least-privilege, confinement |
| 06 | Supply-chain security of agent skills (arXiv 2026) | why signed/verified/fail-closed; DY-Skill threat model |
| 07 | Org capability-growth modelling (Teece; Kogut–Zander; A1.5 lib) | `org_event → capability` accrual; open/combinatorial space |
| 08 | Plugin/extension registry (VS Code) | manifest-driven growable registry; record vs loadable split; policy gate |
