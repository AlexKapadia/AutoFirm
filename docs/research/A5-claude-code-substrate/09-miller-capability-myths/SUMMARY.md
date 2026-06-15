# SUMMARY — Capability Myths Demolished (object-capability security foundation)

## Full citation
- **Title:** "Capability Myths Demolished"
- **Authors:** Mark S. Miller; Ka-Ping Yee; Jonathan Shapiro
- **Year:** 2003
- **Venue/Publisher:** Technical Report SRL2003-02, Systems Research Laboratory, Johns Hopkins
  University (also distributed via combex/agoric)
- **URL/PDF:** https://papers.agoric.com/assets/pdf/papers/capability-myths-demolished.pdf
  (summary corroboration: https://blog.acolyer.org/2016/02/16/capability-myths-demolished/ ;
  https://en.wikipedia.org/wiki/Capability-based_security)

## Questions informed
- **L1.A5.3** Tool/permission model & sandboxing — provides the FOUNDATIONAL THEORY for why
  Claude Code's per-tool/per-subagent capability scoping (sources 02, 05, 06) is the correct
  security model, and what failure (confused deputy) it must prevent. Also grounds A7.3
  (least-privilege / fail-closed) and A8.3 (credential scoping).

## GRADE tier
**High** — a widely-cited primary technical report by the originators of the object-capability
model; foundational, not vendor marketing. Independence: corroborated by independent secondary
sources (Wikipedia, the morning paper summary) and the broader capability-security literature.
This is the peer-reviewed/primary anchor for the security-design claims AutoFirm relies on.

## Key claims (faithful summary; named properties quoted)

1. **Capability defined.** A capability is a communicable, unforgeable token of authority that
   designates an object together with an associated set of access rights — "no designation without
   authority": to name a resource is to hold the authority to use it.

2. **Three properties capability (object-capability) systems have that ACL systems lack:**
   - **Property A — "No Designation without Authority":** "designating a resource always conveys
     its corresponding authority" (designation and authority are coupled; no separate ambient
     namespace).
   - **Property B — dynamic subject creation:** "subjects can dynamically create new subjects"
     (fine-grained subjects down to individual object instances), vs ACLs' coarse principals.
   - **Property C — subject-aggregated authority management:** the power to edit authorities is
     aggregated *by subject* in capability systems (vs ACLs aggregating *by resource*).
   (The paper also relies on a "no ambient authority" property, sometimes labeled D.)

3. **Confused-deputy claim (load-bearing).** A confused deputy is a program that manages
   authorities coming from multiple sources and can be manipulated into wielding authority
   inappropriately (original example: a compiler tricked into overwriting a billing/log file it
   had ambient authority to write but the caller did not). The paper's claim: **without the
   "no ambient authority" + "no designation without authority" properties, confused-deputy attacks
   cannot be prevented; object-capability systems prevent them by coupling designation with
   authority and removing ambient authority.**

4. **Principle of least authority (POLA).** Capability systems take least-privilege to its logical
   conclusion: a subject holds exactly the capabilities it was explicitly granted, enabling
   fine-grained, transferable, revocable authority.

## Reproducibility note
The PDF is the primary artifact (binary; bibliographic + property details corroborated via the
morning-paper summary and Wikipedia's capability-based-security article, both fetched 2026-06-15).
Property names A/B/C and the confused-deputy definition are reproduced from those independent
summaries; the verbatim Property-A phrasing "designating a resource always conveys its
corresponding authority" appears in the summary. For full equation/quote fidelity, consult the
SRL2003-02 PDF directly.
