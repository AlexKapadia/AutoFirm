# BEST-PARTS — Frank & Goyal (2009)

## ADOPT

- **Adopt the six reliable factors as the FEATURE SET for any leverage recommendation** on
  established (post-revenue, asset-holding) clients: industry leverage (+), market-to-book (-),
  tangibility (+), profitability (-), firm size (+), expected inflation (+). These give the engine an
  evidence-backed, multi-source basis for "how much debt is normal for a firm like this".
- **Adopt industry-median leverage as the single strongest anchor.** The most reliable factor is
  *median industry leverage* — so AutoFirm should benchmark a client's target leverage against its
  **industry peers** (ties straight to B12 industry parameterization and NAICS/GICS in L1.B12.2).
- **Adopt the verdict that supports a HYBRID stance:** trade-off explains established firms reasonably
  well, while the negative profit-leverage sign keeps the pecking order alive. The playbook should be
  a **hybrid** (trade-off target band + pecking-order ordering), not a single-theory engine
  (CLAUDE.md §3.5).

## REJECT

- **Reject applying these coefficients to early-stage startups verbatim.** The sample is large public
  US firms, 1950-2003 — indirect for pre-IPO clients. Use the *factor structure* (which variables
  matter, and their signs) as a prior, but do not transplant magnitudes onto startups.

## Concrete build implication

- **Component:** `leverage_benchmark` uses industry-median leverage + the firm's tangibility/
  profitability/size to produce a peer-anchored target band; consumes the same industry parameter as
  the rest of the B12 generalization layer.
- **Test:** sign tests — increasing tangibility raises the recommended leverage; increasing
  profitability lowers external-financing need (matching the paper's signs). A teeth-having check
  that the model reproduces the documented empirical directions, not arbitrary outputs.
