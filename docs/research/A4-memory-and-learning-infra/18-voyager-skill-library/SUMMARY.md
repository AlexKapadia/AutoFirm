# SUMMARY — Voyager: An Open-Ended Embodied Agent with Large Language Models

## Full citation
- **Title:** Voyager: An Open-Ended Embodied Agent with Large Language Models
- **Authors:** Guanzhi Wang, Yuqi Xie, Yunfan Jiang, Ajay Mandlekar, Chaowei Xiao, Yuke Zhu,
  Linxi Fan, Anima Anandkumar
- **Year:** 2023 (arXiv); published **TMLR 2024** (peer-reviewed)
- **Venue:** Transactions on Machine Learning Research (TMLR) 2024
- **arXiv ID / URL:** arXiv:2305.16291 — https://arxiv.org/abs/2305.16291

## Questions informed
- **L1.A4.3** Learning-over-time — covers the **RL-on-memory / lifelong-skill-acquisition** family
  the ontology names explicitly. **Primary** anchor for "learning as an ever-growing, retrievable
  skill memory WITHOUT gradient updates," independent of Reflexion (10) and ExpeL (11).

## Key claims (faithful)
1. **Skill library as lifelong memory (exact):** Voyager builds "an ever-growing skill library of
   executable code for storing and retrieving complex behaviors." Each learned skill is a verified,
   reusable program indexed by an embedding of its description.
2. **No model fine-tuning:** Voyager "interacts with GPT-4 through blackbox queries," avoiding
   parameter updates entirely — learning happens in *external memory* (the skill library), not in
   weights. Skills are "temporally extended, interpretable, and compositional," which "compounds the
   agent's abilities rapidly and alleviates catastrophic forgetting."
3. **Curriculum + self-verification loop:** an automatic curriculum proposes goals; an environment-
   feedback / self-verification step gates whether a new skill is *correct* before it is committed to
   the library — i.e. only verified experience is written to memory.

## GRADE tier
- **High.** Peer-reviewed (TMLR 2024), widely replicated, on-topic for experience/skill memory.
  Indirectness note: domain is embodied (Minecraft), so the *mechanism* (verified-skill memory,
  blackbox LLM) transfers to AutoFirm but the specific task numbers do not — down-rated only for
  use as a *domain-transfer* claim, not for the mechanism itself.

## Why this strengthens the body of evidence
SYNTHESIS L1.A4.3 named an "RL-on-memory" family but cited no primary for it, and *rejected*
parametric RL without a cited alternative. Voyager is the missing **primary** for the
learn-without-gradients-via-an-external-skill-store family — giving L1.A4.3 a *third* independent
peer-reviewed pillar (Reflexion 10 + ExpeL 11 + Voyager 18) and closing the silent-omission gap
(DEPTH-RUBRIC §4: name and cite the surveyed alternative, don't omit it).

## Reproducibility note
Skill-library construction, the blackbox-LLM claim, and the self-verification gate are described in
the methods section + Fig. of the paper at the arXiv URL; code is open-sourced by the authors.
