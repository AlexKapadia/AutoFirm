# BEST-PARTS — IP foundations

## ADOPT
- **A1. IP-asset register as a typed artifact.** AutoFirm's legal playbook maintains, per company, an
  **IP register** classifying each asset into `{patent, copyright, trademark, trade_secret,
  industrial_design, geographical_indication}` with the **protection mechanism and required action**
  per type (file/register vs. automatic vs. secrecy-controls). Build implication: a deterministic
  classifier that, given an asset description, names the protection type and the next legal step.
- **A2. Trade-secret protection = enforce the "reasonable secrecy steps" invariant in the DATA LAYER.**
  Because trade-secret status **legally depends on reasonable steps to maintain secrecy** (WIPO + DTSA),
  AutoFirm's existing public/private workspace boundary (A6.4) is not just good hygiene — it is the
  **legal precondition** for trade-secret protection. Drives a test: company-confidential IP must be
  provably unreachable from the public repo (ties A6.4 ↔ B10).
- **A3. Copyright-on-fixation default.** Treat original authored works as **copyright-protected from
  creation** (no registration needed for the right) — but flag registration as a recommended
  enforcement step. Feeds source 09's caveat that **AI-generated** content may lack human authorship.

## REJECT / DEFER
- **R1. REJECT a one-size IP strategy.** The four types are **mutually exclusive in mechanism**
  (patent = disclose-for-monopoly; trade secret = never disclose). The engine must not recommend
  patenting something whose value depends on secrecy — these are opposed strategies. A naive "protect
  everything the same way" rule is a FAIL.
- **R2. DEFER per-jurisdiction filing procedure** (USPTO vs. EPO vs. national offices) to the
  jurisdiction module — L1 fixes the *taxonomy*, not the filing mechanics.

## Build implication (concrete)
- **Component:** `legal/ip/ip_register.py` + `ip_strategy_recommender`.
- **Contract:** `IPAsset{ type, protection_mechanism, action_required, secrecy_controls_enforced: bool,
  jurisdiction }`.
- **Test:** patent-vs-trade-secret conflict case (an asset valued for secrecy must NOT be recommended
  for patenting); trade-secret asset must assert the secrecy-controls invariant true before status is
  granted (boundary on the legal precondition).
