# BEST-PARTS — DAMA-DMBOK Roles → AutoFirm's Organizer/Librarian

## ADOPT
1. **Model AutoFirm's "organizer/librarian" as a DMBOK Data STEWARD agent** — the business-side
   keeper that ensures "content and metadata are consistent with the organization's policies,
   standards, and business rules." Concretely this agent: maintains the folder taxonomy + naming,
   classifies each artifact (PUBLIC vs PRIVATE, source 02/03), owns the `.gitignore` and
   `.gitleaks.toml` allowlists, and audits boundary-guard findings. This is the role half of A6.4.
2. **Separate the three responsibilities** (owner / steward / custodian) into distinct, least-
   privilege agent capabilities (CLAUDE.md §5.6 least-privilege):
   - **Data Owner** = the company/CTO orchestrator — accountable, sets the classification policy.
   - **Data Steward (organizer/librarian)** = keeps structure + boundary + metadata consistent;
     read/move within workspaces, edit taxonomy/allowlists — but NOT delete sensitive data silently.
   - **Data Custodian** = the storage/ops layer — backup, encryption-at-rest, retention, recovery
     of the private store (sources 09/10).
   Separation prevents one over-powered agent (matches §5.6 "no shared god-keys").
3. **Stewardship is continuous, policy-driven, and audited** — the librarian runs on the
   organizer/North-Star heartbeat (CLAUDE.md §4.7), re-checking that structure + boundary still hold
   and logging every reclassification/move to the append-only audit log (A6.2).

## REJECT / QUALIFY
- **Reject heavyweight committee/council governance** (stewardship-domain meetings, councils) from
  DMBOK — overkill for an autonomous agent system. Take the *role definitions + separation
  principle*, not the human org-chart ceremony.

## Concrete build implication
- **Component:** `organizer-librarian` steward agent + a `custodian` storage service; owner = orchestrator.
- **Contract:** steward may classify/move/rename and edit taxonomy + allowlists, must log every act,
  and must escalate (not silently delete) sensitive data (mirrors CLAUDE.md §3.8 dead-code rule).
- **Test:** an authorization test asserting the steward agent CANNOT exfiltrate/commit PRIVATE data
  and CANNOT delete it un-audited; a heartbeat test asserting structure/boundary drift is flagged.
