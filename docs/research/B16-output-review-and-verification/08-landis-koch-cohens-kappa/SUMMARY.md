# 08 — Landis & Koch, *The Measurement of Observer Agreement for Categorical Data* (Cohen's / Fleiss' kappa)

- **Authors / org:** J.R. Landis & G.G. Koch (interpretation bands); Jacob Cohen (1960, the statistic).
- **Year:** Cohen 1960 (*Educ. Psychol. Meas.* 20:37–46); Landis & Koch 1977 (*Biometrics* 33:159–174).
- **Link:** Landis & Koch via PMC/NCBI; widely reproduced.
- **Tier:** High — foundational inter-rater-reliability statistics.

## Faithful structured summary

**Cohen's kappa** measures agreement between two raters on categorical labels **corrected for
chance agreement**:

  **kappa = (p_o - p_e) / (1 - p_e)**

where **p_o** = observed proportion of agreement and **p_e** = proportion expected by chance.
kappa = 1 is perfect agreement; kappa = 0 is chance-level; kappa < 0 is worse than chance.
(**Fleiss' kappa** generalises to >2 raters — e.g. a jury vs a panel of gold reviewers.)

**Landis & Koch (1977) interpretation bands (verbatim):**
- < 0.00 : poor
- 0.00–0.20 : slight
- 0.21–0.40 : fair
- 0.41–0.60 : moderate
- 0.61–0.80 : substantial
- 0.81–1.00 : almost perfect

**Professional convention:** kappa >= 0.61 (substantial) is commonly the acceptability floor;
high-stakes/clinical journals (BMJ, JAMA, Lancet) typically expect **kappa > 0.70**, and many editors
treat **< 0.60** as reason to doubt the review process.

## Best parts to take (for our gate) and why

1. **kappa is the headline evidence metric for the gate.** Report **gate-verdict vs gold-human-reviewer
   kappa** on a labelled golden set. Because our gate is largely deterministic and our gold labels are
   verified, target **kappa >= 0.80 ("almost perfect")** on the must-block defect classes — far above
   the 0.61 floor used for subjective tasks.
2. **Chance-correction matters:** raw "% agreement" is inflated when most artifacts pass; kappa is the
   honest number to put in `evidence/`.
3. **Use it to set the bar for any model-advisory layer:** the layer earns its place only if it
   *raises* gate-vs-human kappa on the residual (semantic) class without lowering it elsewhere — a
   measurable, evidence-gated admission criterion (CLAUDE §3.4).
