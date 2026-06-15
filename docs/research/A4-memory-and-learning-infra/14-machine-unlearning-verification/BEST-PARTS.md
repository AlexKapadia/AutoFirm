# BEST-PARTS — Machine Unlearning Verification

## ADOPT
- **Verified Forgetting must produce an auditable artifact, not a "we deleted it" log line.** Build
  implication: AutoFirm's VF primitive (from folder 12) deletes the record AND emits a verifiable
  deletion artifact (e.g., proof the embedding/index entry is gone + a post-deletion non-recoverability
  check), written to the append-only audit log (A6). Satisfies regulator-grade scrutiny (CLAUDE.md s3.2).
- **Prefer EXACT deletion for AutoFirm's external memory.** Crucial simplification: because AutoFirm's
  durable memory is an EXTERNAL index/DB (folder 05 parametric/non-parametric split), not baked into
  model weights, AutoFirm can do *exact* deletion (drop the record + reindex) and sidestep the hard,
  unreliable approximate-weight-unlearning problem entirely. This is a strong architectural argument
  FOR external memory.
- **Treat "deleted but recoverable" as a defect.** The reversibility finding means a deletion test
  must assert non-recoverability (query after delete returns nothing, including via near-duplicate
  embedding queries).

## REJECT / DEFER
- **Reject approximate weight-level unlearning as AutoFirm's deletion path** — unreliable and
  unverifiable for a hosted model; rely on external-store exact deletion instead.

## Build implication (concrete)
Specifies that **Verified Forgetting = exact external-store deletion + an auditable
non-recoverability proof**, turning the VF primitive (folder 12) into a testable, regulator-defensible
control — and provides a second independent justification for keeping durable memory external (folder 05).
