# Toward an integrated workforce planning framework using structured equations

**Question informed:** L1.A1.5 (gap-detect -> spawn -> retire lifecycle); feeds L2.ORG.

## Full citation
- **Title:** Toward an integrated workforce planning framework using structured equations
- **Authors:** Marie Doumic, Benoit Perthame, Edouard Ribes, Delphine Salort, Nathan Toubiana
- **Year:** 2016 (v2, 2 Dec 2016)
- **Venue:** arXiv preprint arXiv:1607.02349v2 [q-fin.GN]
- **URL:** https://arxiv.org/abs/1607.02349 ; PDF https://arxiv.org/pdf/1607.02349
- **GRADE tier:** **Moderate** (arXiv preprint with full methods + closed-form math + empirical
  results; authors at Inria/Sorbonne/CNRS). Up-rated for self-contained, reproducible
  derivations; not down-rated because the load-bearing claims are the *equations* themselves
  (verifiable verbatim from the text), not contested empirical effects.

## What it is
A quantitative framework for **Strategic Workforce Planning (SWP)** built on *structured
population dynamics* (the age-structured McKendrick-Von Foerster renewal equation). It answers
two operational questions: (1) how to hire optimally to keep labour cost flat; (2) how to build
an experience-constrained workforce at minimal cost.

## Key claims (exact, with locators)

**Definition of SWP (Sec.1, Introduction).** Quoted: "Strategic Workforce Planning (SWP)
examines the **gap between staff availabilities** (internal and external to the organization)
**and staffing requirements** (to perform tasks in the organization) **over time, and
prescribes courses of action to narrow such a gap**." => gap = requirement - availability,
over time.

**The 5 milestones of SWP (Sec.1, citing refs [25,29]).** Reproduced:
1. **Baselining** the population.
2. **Demographic forecasts** drafted to assess the potential evolution of headcount.
3. **Business needs** gathered - both **headcount and competencies**.
4. **Gap analysis** between the company's desired future state and its natural evolution.
5. **Solutions to bridge the gaps** proposed, agreed upon, and implemented.

**Implementation failure base-rates (Sec.1, citing CEB benchmarks [1,14]).** "only **10%** of
companies really succeed in aligning their workforce plans to meet strategic objectives. ...
**70%** failed at drafting a workforce plan and **84%** ... are not confident in their use of
labor market trends. ... **65%** of the respondents felt a disconnection between the business
needs and standard Human Resources processes such as recruitment."

**The governing age-structured workforce equation (Sec.2).** Reproduced exactly in the source's
notation; rho(t,z) = density of workers of age/tenure z at time t, z in [z_min, z_max]:

    d/dt rho(t,z) + d/dz rho(t,z) = - mu(z) rho(t,z) + h(P_t) P_t beta(z),   z_min < z < z_max

- **mu(z)** = attrition rate (exogenous: market demand, terminations, retirement).
- **h(P_t) P_t beta(z)** = hiring term; **beta(z)** = hiring age/tenure distribution (the
  "hiring profile"); **P_t = integral_{z_min}^{z_max} rho(t,z) dz** = total headcount.
- **Retirement** modelled as a hard boundary: at z_max the worker leaves the active workforce.

**Saturating hire rate (Sec.2.1).** To prevent exponential blow-up/decay (the Malthusian linear
case), they choose the saturation form **h(P_t) = 1 / (1 + P_t^2)**, giving convergence toward a
stable equilibrium age profile **P_eq**.

**Two movements rule evolution (Sec.2):** **attrition** (exogenous - leavers) and **hiring**
(endogenous - depends on firm activity). Attrition is driven by three factors: market labour
demand, company termination policies, and retirement.

**State of the art (Sec.1):** SWP emerged in the 1970s; the field is dominated by **stochastic
formalisms - Markov chains and stochastic linear programming, game theory, convex
approximation** - with optimal-hiring-policy studies (e.g. Anderson's apprentice/experienced
ratio optimisation). PDE/structured-population approaches are noted as "very marginal" prior to
this work.

## Up/down-rate reasoning
The relied-upon items are the **definition**, the **5 milestones**, and the **equation form** -
all quoted directly, so confidence is high *for what the paper says*. The CEB base-rate
percentages are second-hand (the paper cites CEB), so they are tagged supporting/contextual and
are corroborated by the broader SWP literature (source 02).

## Reproducibility note
A reviewer can re-derive the milestone list and the equation directly from Sec.1 and Sec.2 of
the arXiv PDF (text extracted verbatim above). The equation is the standard McKendrick-Von
Foerster renewal equation with an age-dependent death rate and a saturating birth (hire) term.
