# BEST-PARTS — FIPS 199 → AutoFirm

## ADOPT
1. **Classify every datum on the confidentiality axis BEFORE deciding which side of the boundary
   it goes.** AutoFirm's public/private split is precisely a binary collapse of the FIPS-199
   **confidentiality** dimension: anything whose unauthorized disclosure has more than LOW impact
   (i.e. MODERATE/HIGH — "serious" / "severe or catastrophic") is **private** and may never enter
   the public repo. **Build implication:** a `data-classifier` contract that stamps each artifact
   with `{confidentiality: LOW|MODERATE|HIGH}` and routes MODERATE/HIGH to the gitignored private
   workspace fail-closed.
2. **High-water-mark rule for whole workspaces.** A per-company workspace that contains ANY
   MODERATE/HIGH-confidentiality artifact is itself classified MODERATE/HIGH → the entire workspace
   directory is gitignored and stored in the governed store. This prevents a "mostly-public folder
   with one secret file" leak. **Build implication:** the organizer/librarian classifies at the
   workspace root by the max of its contents (source 02 high-water-mark).
3. **CIA, not just C.** Keep integrity + availability impact too: the **append-only audit log**
   (A6.2) is HIGH-integrity; losing it is a HIGH-integrity event. Drives which stores get tamper-
   evidence and backups.

## REJECT / QUALIFY
- **Reject importing all of FIPS-199/SP-800-53's federal control catalog wholesale.** AutoFirm
  needs the *categorization model*, not the full FedRAMP control overhead. Adopt the SC triplet +
  high-water-mark; leave the control-selection machinery to A7/A8 where it belongs.

## Concrete build implication
- **Component:** `classification` module emitting the SC triplet per artifact + per workspace.
- **Contract:** `SC = {(confidentiality, impact),(integrity, impact),(availability, impact)}`,
  impact ∈ {LOW,MODERATE,HIGH}; `confidentiality >= MODERATE ⇒ private`.
- **Test:** boundary-exact tests at the LOW/MODERATE cutoff (a LOW datum may be public; a MODERATE
  datum at the same key must be routed private) — proving the cutoff is enforced, not assumed.
