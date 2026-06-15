# SUMMARY — LegalBench: benchmarking legal reasoning in LLMs

## Full citation
- **Guha, N., Nyarko, J., Ho, D. E., Ré, C., Chilton, A., Narayana, A., Chohlas-Wood, A., Peters, A.,
  Waldon, B., Rockmore, D. N., Zambrano, D., Talisman, D., Hoque, E., Surani, F., Fagan, F., Sarfaty, G.,
  Dickinson, G. M., Porat, H., Hegland, J., Wu, J., Nudell, J., Niklaus, J., Nay, J., Choi, J. H., Tobia,
  K., Hagan, M., Ma, M., Livermore, M., Rasumov-Rahe, N., Holzenberger, N., Kolt, N., Henderson, P.,
  Rehaag, S., Goel, S., Gao, S., Williams, S., Gandhi, S., Zur, T., Iyer, V., & Li, Z. (2023).**
  *LegalBench: A Collaboratively Built Benchmark for Measuring Legal Reasoning in Large Language Models.*
  arXiv:2308.11462 [cs.CL] (Aug 20, 2023). Also published at **NeurIPS 2023** (37th Conf. on Neural
  Information Processing Systems, Datasets & Benchmarks Track), DOI 10.5555/3666122.3668037.
  URL: https://arxiv.org/abs/2308.11462

## Ontology questions informed
- **L1.B10.1** — evidence on whether LLM agents can *reliably do legal reasoning* (the capability
  question underlying any automated legal/compliance playbook). Feeds **L2.B10** (what legal tasks may
  be automated vs. must escalate) and **L1.A9** (eval rigor).

## GRADE tier
- **High.** Peer-reviewed (NeurIPS 2023 Datasets & Benchmarks) + arXiv; tasks **hand-crafted by legal
  professionals** (40 contributors). Strong methods + results. No down-rate for the existence/structure
  claims. (For specific per-model accuracy numbers, treat as **point-in-time** — models evolve.)

## Key claims (with locators)
1. **Scale & structure:** LegalBench consists of **162 tasks** covering **six types of legal reasoning**,
   built by **40 contributors** (abstract).
2. **Six reasoning categories** (paper §3 taxonomy): **issue-spotting, rule-recall, rule-application,
   rule-conclusion, interpretation, and rhetorical-understanding.** These map to the **IRAC framework**
   (Issue, Rule, Application, Conclusion) used by lawyers (paper §3).
3. **Expert-built validity:** tasks were "designed and hand-crafted by legal professionals", so they
   measure **practically useful** legal reasoning, not synthetic proxies (abstract / §1).
4. **Empirical evaluation:** the paper presents an empirical evaluation of **20 open-source and
   commercial LLMs** (abstract). Performance varies widely across the six reasoning types — models are
   stronger on rule-recall/issue-spotting than on multi-step rule-application and interpretation (paper
   results discussion). [Exact per-model numbers are in the paper's results tables; treat as dated.]
5. **Purpose:** answer "what types of legal reasoning can LLMs perform?" — i.e., a **capability map**,
   explicitly to inform responsible deployment, not a claim that LLMs are competent lawyers.

## Corroboration
- Corroborated by **LawBench** (Fei et al., 2023, arXiv:2309.16289) and the survey *Evaluation of LLMs
  in Legal Applications* (arXiv:2601.15267), which independently find **uneven LLM legal performance**
  and the need for task-specific evaluation — ≥3 independent sources for the "LLM legal reasoning is
  uneven / task-dependent" claim.

## Reproducibility note
A reviewer re-derives the 162-task / six-category structure and the IRAC mapping from the arXiv abstract
and §3 of the paper; per-model accuracy is reproducible by running the open LegalBench harness (released
with the paper). Numbers should be cited with the model + date, never as timeless facts.
