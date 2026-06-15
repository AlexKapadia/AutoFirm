# SUMMARY — Erlang C queueing model for support staffing & service levels

## Full citation
- **Primary origin:** A. K. Erlang (1917), queueing-theory work on telephone-traffic congestion (Erlang C delay formula), Copenhagen Telephone Company. Foundational paper: Erlang, A. K. (1917), "Solution of some problems in the theory of probabilities of significance in automatic telephone exchanges," *Post Office Electrical Engineers' Journal*.
- **Standard professional references (verification):**
  - The Call Centre Helper / NICE, *Erlang C Formula*, https://www.nice.com/glossary/erlang-c-formula
  - TechTarget, *What is Erlang C*, https://www.techtarget.com/searchunifiedcommunications/definition/Erlang-C
  - Society of Workforce Planning Professionals (SWPP), *Calculating Call Center Staff*, https://swpp.org/certification/articles/calculating-call-center-staff/

## Ontology question informed
- **L1.B9.1** — the quantitative basis for SLA-feasible staffing (the link between SLA targets and capacity).

## What the source claims (faithful)
- **Erlang C** models an inbound queue (M/M/c): calls arrive (Poisson), are served by `c` agents, and **wait in queue** if all agents are busy until one frees up (no abandonment in the base model).
- **Traffic intensity (offered load), in Erlangs:** `A = λ × AHT`, where `λ` = arrival rate (calls per unit time) and `AHT` = average handle time (same time unit).
- **Erlang C probability of waiting** (probability a call is queued) for `c` agents and load `A`:
  `P_wait = ( A^c / c! · c/(c−A) ) / ( Σ_{k=0}^{c−1} A^k/k! + A^c / c! · c/(c−A) )`  (requires `c > A` for stability).
- **Service level** (probability a call is answered within target wait `t`):
  `SL(t) = 1 − P_wait · e^{ −(c − A)·t / AHT }`.
- **Industry-standard "grade of service":** the **80/20** target — **80% of calls answered within 20 seconds** — is the canonical service-level benchmark, balancing wait time against staffing cost.
- **Agent occupancy:** `ρ = A / c` (utilisation); high occupancy reduces cost but increases wait and burnout risk.

## Source-quality grade (GRADE-adapted)
- **Tier: High (for the mathematics).** Erlang C is a peer-established, century-old queueing-theory result, universally used in workforce management. The **80/20 benchmark** itself is a **convention** (Moderate), not a derived optimum.
- **Down-rate (scope):** base Erlang C ignores abandonment (Erlang A / Erlang X extend it) and assumes stationary Poisson arrivals; real demand is non-stationary. Use as a capacity *estimate*, not an exact predictor.

## Reproducibility note
The Erlang C waiting-probability and service-level formulae are standard and reproducible from any queueing-theory text (e.g. M/M/c). The 80/20 target is documented as the industry-standard benchmark by SWPP and the cited professional references. The non-stationary-arrival caveat is documented in the workforce-management literature (e.g. arXiv:0807.4071, forecasting inhomogeneous Poisson call-centre demand).
