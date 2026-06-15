# BEST-PARTS — ExpeL

## ADOPT
- **Cross-trajectory insight abstraction as AutoFirm's "Experience" tier** (the top of the
  Storage->Reflection->Experience model, folder 01). Build implication: after many client builds,
  AutoFirm runs an insight-extraction pass that distills **industry-agnostic, reusable lessons**
  (e.g., "for regulated fintech clients, do X before Y") into the procedural/semantic store — the
  concrete mechanism behind "AutoFirm gets better at building companies over time" and behind
  generalization (L1.B12).
- **No-parametric-update learning is the correct frame for a hosted-model platform** — corroborates
  Reflexion (folder 10) with an independent group, satisfying the >=2-source bar for the
  "learn-without-fine-tuning" architecture choice.
- **k-NN recall of similar past tasks + insight set at inference** = the retrieval contract for the
  experience tier (reuses the dense retriever, folders 03/07).

## REJECT / DEFER
- **Reject naive insight accumulation without curation/conflict-resolution.** Insights can conflict
  or become stale across industries; AutoFirm must version, scope (per-industry), and validate
  insights before reuse (ties to A4.4 provenance + A6 audit) — otherwise an over-general insight
  overfits one client (CLAUDE.md s3.9).

## Build implication (concrete)
Defines the **Experience tier = cross-trajectory insight extraction**, scoped + versioned, retrieved
by k-NN at inference; corroborates the **no-fine-tune learning decision** for L2.A4 with a second
independent peer-reviewed source.
