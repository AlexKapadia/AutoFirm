# BEST-PARTS — NAICS Conceptual Framework

## ADOPT
1. **Confirms the prefix-fallback parameterization design (source 01 BEST-PARTS).** Two independent
   official agencies confirm 2->6 digit = sector->national-industry. AutoFirm's longest-prefix
   playbook resolver is therefore standing on a corroborated (>=2 independent High-tier sources)
   structural claim, satisfying DEPTH-RUBRIC for an "important" architecture claim.
2. **The 6th-digit-is-country-specific fact -> AutoFirm keys at 5 digits.** Adopt the 5-digit
   internationally-comparable level as the default playbook key so the platform is not US-locked;
   reserve the 6th digit for explicit national overrides only.

## REJECT
1. **REJECT relying on NAICS counts as fixed.** Counts of subsectors/industries change every 5-year
   revision (2017->2022->2027). Do not hard-code the number of codes; resolve dynamically against a
   loaded NAICS table so a future vintage does not break the resolver.

## Build implication
Corroborating evidence (not a new mechanism). Drives a unit test that the prefix-fallback resolver
treats digit positions exactly as sector(2)/subsector(3)/group(4)/industry(5)/national(6), and that
the resolver is vintage-agnostic (loads the code table rather than hard-coding it).
