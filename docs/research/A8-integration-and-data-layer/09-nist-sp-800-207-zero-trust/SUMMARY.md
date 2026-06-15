# SUMMARY — NIST SP 800-207: Zero Trust Architecture

## Full citation
- **Title:** Zero Trust Architecture.
- **Authors:** Scott Rose, Oliver Borchert, Stuart Mitchell, Sean Connelly (NIST).
- **Year:** August 2020.
- **Venue/Publisher:** NIST Special Publication 800-207.
- **URL/DOI:** https://csrc.nist.gov/pubs/sp/800/207/final · https://doi.org/10.6028/NIST.SP.800-207

## Questions informed
- **L1.A8.3** Secrets & credential scoping for autonomous agents (per-session, least-privilege, dynamic-policy credentialing).
- Supporting for **L1.A8.1/A8.2** (deny-by-default, per-request authorization).

## GRADE tier
**High.** Official, foundational U.S. government standard for zero trust.

## Key claims (tenets, with locators)
1. **Per-session, least-privilege access (tenet):** "Access to individual enterprise resources is granted on a per-session basis," with "access granted using the least privileges needed to complete the task." Privileges are time-bound and elevated only when necessary, authorized only for the duration of that task/session — preventing indefinite privileges.
2. **Dynamic policy (tenet):** access is "determined using dynamic policy" informed by context — identity assurance level, privilege level, machine/identity posture, recent behavior, device posture, environmental conditions.
3. **Architecture components:** the Policy Decision Point (PDP) = Policy Engine (PE) (allow/deny per request from multiple data sources) + Policy Administrator (PA) (executes the PE decision; configures paths and generates session credentials). Enforced at the Policy Enforcement Point (PEP).
4. **Never trust, always verify; assume breach; verify explicitly** are the governing principles; no implicit trust by network location.

## Up/down-rate reasoning
- Up-rated: foundational official standard; directly on-point for "credentials issued per session, scoped to task, dynamically authorized."
- Indirectness: written for enterprise human/device access; applied to AutoFirm by treating each agent session as a ZTA "subject" requiring per-session, least-privilege, dynamically-authorized credentials — a direct mapping.

## Reproducibility note
The seven tenets (incl. per-session least-privilege and dynamic policy) and the PE/PA/PEP model are in SP 800-207 §2 (Tenets) and §3 (Logical Components). Cite by section/tenet number when quoting verbatim.
