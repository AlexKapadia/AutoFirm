# BEST-PARTS — Forbis & Mehta (1981) + Monroe — what AutoFirm adopts

> Adopt/reject decisions tied to cited evidence (DEPTH-RUBRIC §4-5). This folder hardens the
> EVC formula already adopted in source 02 by giving it a peer-reviewed primary origin.

## ADOPT
- **A1. EVC as the canonical WTP-ceiling, now primary-anchored.** AutoFirm's deterministic value
  model keeps `EVC = Reference Value + Differentiation Value - Switching/Implementation Costs`
  (source 02), but its *authority* is now **Forbis & Mehta 1981** (the origin) + **Monroe** +
  Nagle (01) - three independent sources. *Build implication:* the EVC core module's docstring
  cites Forbis & Mehta (1981) as the formula's primary; the value-model contract is unchanged, the
  evidence body is upgraded Low -> Moderate-High. Drives the EVC unit + mutation tests (exact arithmetic).
- **A2. Surplus-equalization framing for the ceiling.** Forbis & Mehta define EVC as the price that
  **equalizes net economic surplus** vs. the next-best alternative. *Build implication:* the engine
  computes EVC as `NBA_price + sum(net_economic_deltas)` and emits a price **strictly below** EVC by
  a configurable value-share fraction (buyer incentive). Encodes invariant 2 in SYNTHESIS (price <= EVC).
- **A3. Two-bucket delta taxonomy (start-up vs life-cycle).** Adopt Forbis & Mehta's split of
  differentiation value into **start-up cost changes** and **post-purchase/life-cycle cost changes**.
  *Build implication:* the EVC input schema exposes these two buckets explicitly, so the
  value-communication artifact (source 01) itemizes savings the way the primary source structures them.
- **A4. Perceived value vs economic value (Monroe).** *Build implication:* the engine distinguishes
  the *economic* EVC ceiling from *perceived/communicated* WTP (source 01 claim 2), and never assumes
  realized WTP = EVC without a value-communication step - reinforces the value-cascade ordering.

## REJECT / DEFER
- **R1. REJECT treating EVC headline numbers as benchmarks.** Forbis & Mehta's worked figures (and
  source 02's) are illustrative; AutoFirm computes EVC per client from real inputs (generality, §3.9).
- **D1. DEFER optimal value-sharing split.** How far below EVC to price (the buyer/seller split) is a
  game-theoretic/negotiation decision -> L2.B5 + sales (B8), not fixed here.

## Test / evidence hooks
- EVC arithmetic exact to the cent; property test: price emitted is always <= computed EVC.
- Citation test: EVC module references Forbis & Mehta (1981) DOI 10.1016/0007-6813(81)90035-0.
