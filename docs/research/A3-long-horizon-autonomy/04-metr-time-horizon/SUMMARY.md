# SUMMARY — METR "Measuring AI Ability to Complete Long Software Tasks"

## Full citation
- **Title:** Measuring AI Ability to Complete Long Software Tasks
- **Authors:** Thomas Kwa, Ben West, Joel Becker, Amy Deng, Katharyn Garcia, Max Hasin, Sami Jawhar, Megan Kinniment, Nate Rush, Sydney Von Arx, Ryan Bloom, Thomas Broadley, Haoxing Du, Brian Goodrich, Nikola Jurkovic, Luke Harold Miles, Seraphina Nix, Tao Lin, Neev Parikh, David Rein, Lucas Jun Koba Sato, Hjalmar Wijk, Daniel M. Ziegler, Elizabeth Barnes, Lawrence Chan (METR)
- **Year:** 2025
- **Venue:** arXiv:2503.14499 (v3); accompanying METR blog (2025-03-19)
- **URL/DOI:** https://arxiv.org/abs/2503.14499 ; https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/

## Ontology questions informed
- **L1.A3.1** Levels-of-autonomy frameworks — provides a *measurable, capability-grounded* autonomy metric (time horizon) complementing the normative ladders (sources 01–03).
- **L1.A3.2** Long-horizon failure modes — quantifies how reliability decays with task length.

## GRADE tier
- **Moderate–High.** arXiv preprint (Moderate by §2) but **up-rated** toward High for the headline metric: rigorous methodology (170 tasks across HCAST + RE-Bench + SWAA, 800+ human baselines from skilled professionals, logistic fit, hierarchical-bootstrap 95% CIs). Down-rate: not yet a peer-reviewed venue; extrapolation/projection claims are speculative and kept out of relied-upon claims.

## Key claims (exact numbers + locators)
- **Definition — 50% time horizon:** the task duration (measured by human-expert completion time) at which a model achieves **50% success probability**, obtained by fitting a logistic curve of success probability vs. human task length.
- **Headline finding (quoted):** "the length of tasks (measured by how long they take human professionals) that generalist frontier model agents can complete autonomously with 50% reliability has been **doubling approximately every 7 months for the last 6 years**."
- **Confidence:** "95% CI calculated by hierarchical bootstrap" (the blog states the method; the arXiv paper gives the numeric bounds).
- **Best-model horizon at publication:** o3 ≈ **110 minutes** (50% time horizon) per the blog/search summary; Claude 3.7 Sonnet ≈ "approximately one hour."
- **Task suite:** "a diverse suite of 170 tasks (HCAST, RE-Bench, and a new suite of Software Atomic Actions — SWAA)" with human times "ranging from seconds to tens of hours"; "over 800 human baselines."
- **Logistic model:** success probability is modeled as a logistic (sigmoid) function of (log) human task length; the exact equation is in the arXiv paper (not reproduced verbatim here — re-derive from arXiv:2503.14499 before relying on the parametric form).

## Reproducibility note
Headline doubling-time (~7 months) and the 170-task / 800-baseline counts are stated in both the blog and arXiv abstract — independently corroborated. **Do not** cite the exact logistic-equation parameters until pulled verbatim from the arXiv PDF (flagged open item). The 110-min o3 figure is from a secondary summary of the blog; verify against arXiv before treating as a relied-upon number.
