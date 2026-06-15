# BEST-PARTS — Autor/Levy/Murnane → AutoFirm

## ADOPT
- **The routine ↔ non-routine × cognitive ↔ manual 2×2 as AutoFirm's first-cut automatability
  classifier.** It is the theoretical backbone behind every later study and is dead simple to
  apply per task. **Build implication:** `automatability/routine_classifier.py` tags each APQC
  Task into one of the 4 quadrants; routine-cognitive + routine-manual → high-confidence full
  automation; non-routine quadrants → augmentation / HITL. This is the cheap, deterministic first
  filter that the richer bottleneck/capability scores (sources 05/06/09) then refine.
- **The substitute-vs-complement framing** is exactly AutoFirm's operating philosophy: agents
  *substitute* on routine tasks and *complement* humans on non-routine ones — design AutoFirm as a
  complement-by-default system (matches McKinsey's <5%-fully-automatable finding). This is a
  durable, pre-LLM-and-post-LLM-valid principle.
- **"Following explicit rules = automatable" criterion** directly informs which AutoFirm internal
  paths must be *deterministic rule engines* (CLAUDE §3.5 deterministic core) vs. which need an
  LLM/soft layer: rule-expressible tasks → deterministic; ambiguous/communicative → LLM layer.

## REJECT / use-with-care
- **Use-with-care: LLMs partially break the original dichotomy.** ALM (2003) classed "complex
  communication" and "non-routine cognitive" as *complemented, not substituted* — generative AI
  now *substitutes* on much of that (source 09). The 2×2 remains the right *axes*, but the
  routine→automatable mapping must be widened: "non-routine cognitive that is nonetheless
  text/knowledge-based" is now substitutable. Do not treat the 2003 boundary as fixed.
- **Reject the manual-vs-cognitive split as primary for a software agent company.** AutoFirm
  builds/operates companies via software; *manual* tasks are out of its direct scope (delegated to
  the client's physical operations). The *routine vs. non-routine* axis is the load-bearing one for
  AutoFirm; the manual axis mostly flags "needs a human/robot, not an agent".

## Concrete build implication
- Component: `automatability/routine_classifier.py` — deterministic 4-quadrant tagger feeding the routing decision (deterministic-rule-engine vs. LLM-soft-layer vs. HITL).
- Test it drives: a determinism + property test that rule-expressible tasks always route to the deterministic engine, and a metamorphic test that reclassifying a text-based "non-routine cognitive" task post-LLM-uplift moves it from complement to substitute (proving the boundary was widened, not hard-coded to 2003).
