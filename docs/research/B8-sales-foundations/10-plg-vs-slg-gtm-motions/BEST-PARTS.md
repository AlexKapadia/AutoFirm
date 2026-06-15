# BEST-PARTS — PLG vs SLG vs PLS (GTM motions)

## ADOPT
- **Adopt the PLG↔PLS↔SLG motion spectrum as AutoFirm's TOP-LEVEL sales-motion selector**, sitting above methodology selection (source 09). The agent first picks a *motion* (no-touch / hybrid / high-touch) from product type, ACV, and buyer (B2C-ish self-serve vs complex B2B), THEN picks a methodology within it. *Build implication:* `SalesMotion` enum {PLG, PLS, SLG} drives whether the agent provisions a self-serve funnel + PQL scoring, a rep-led MEDDPICC pipeline, or both.
- **Adopt PQL scoring for any self-serve/PLG motion** — an in-product behavioural threshold that triggers either auto-conversion or rep hand-off. This is the self-serve analogue of the buying-center qualification and is fully automatable. *Build implication:* `pql_score` component in the PLG path; threshold crossing → expansion play (PLS).
- **Adopt hybrid/PLS as the DEFAULT for B2B SaaS** (McKinsey + source 07): land via self-serve, expand via reps — matching the rule-of-thirds (offer all channels) and the rep-free-preference data (source 06).

## REJECT
- **Reject mandating PLG everywhere.** PLG requires a product whose value is self-evident quickly and low-friction to try — false for high-touch services, regulated/complex sales, or physical goods (several B12 panel rows). Motion must be SELECTED, not defaulted.
- **Reject PLG benchmark numbers as hard facts** — they are practitioner/VC data; cite the taxonomy, prove conversion numbers on AutoFirm's own golden set.

## Why this matters for generality
The motion spectrum is the cleanest mechanism for spanning the B12 panel: a B2B-SaaS (row 1) defaults PLS, discrete manufacturing (row 3) defaults SLG, DTC e-commerce (row 4) defaults PLG/self-serve. ONE selector parameterizes the entire panel — generality by design, not overfitting to one company.
